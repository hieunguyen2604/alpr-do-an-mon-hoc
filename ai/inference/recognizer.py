"""PaddleOCR-backed implementation of :class:`~ai.inference.interfaces.BaseRecognizer`.

This module reads the characters off a cropped plate. It does **not** correct
or validate them: that is :class:`~ai.inference.interfaces.BaseNormalizer`'s
job, and keeping the two apart is what makes the contribution of
post-processing measurable (``raw_ocr_text`` versus ``plate_number`` in
``detection_history``).

Choice of engine -- and an honest caveat
----------------------------------------
PP-OCRv5 mobile is used as the **baseline**, not as a proven optimum. The
Phase 1 survey found *no* public evidence that PaddleOCR outperforms EasyOCR on
license-plate imagery; the one reproducible comparison that was located
actually favoured EasyOCR. Presenting PaddleOCR as "the accurate one" would
therefore be unsupported.

This is precisely why :class:`~ai.inference.interfaces.BaseRecognizer` exists.
Adding an EasyOCR recogniser means writing a second subclass in this package
and changing which one is constructed at start-up -- nothing else in the
pipeline, the services or the routers moves. The Phase 4 benchmark, run on this
project's own dataset, is what decides which engine ships.

Two-line plates
---------------
The hard case (risk R-04) is delegated to :mod:`ai.inference.two_line`: a crop
whose aspect ratio suggests two rows is split into overlapping halves and
re-stacked side by side into a single-line strip before OCR runs. See that
module for why this is necessary.
"""

from __future__ import annotations

import logging
import os
import time

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from typing import Any, Final, Sequence

import numpy as np

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import (
    InvalidImageError,
    ModelLoadError,
    RecognitionError,
)
from ai.inference.interfaces import BaseRecognizer
from ai.inference.two_line import (
    estimate_line_count,
    merge_two_line,
    preprocess_plate,
    split_two_line,
)
from ai.inference.types import ImageArray, PlateRecognition

__all__ = [
    "OCR_VERSION",
    "DEFAULT_ENABLE_MKLDNN",
    "OCR_INPUT_HEIGHT",
    "PaddleOcrRecognizer",
]

_LOGGER = logging.getLogger(__name__)

OCR_VERSION: Final[str] = "PP-OCRv5"
"""PP-OCR generation this recogniser pins.

Pinned rather than left to the library default so that a PaddleOCR upgrade
cannot silently change the models behind a published benchmark number.

.. warning::

   ``lang="en"`` plus this version does **not** by itself yield an all-mobile
   pipeline. Phase 7 measured the resulting engine loading
   ``PP-OCRv5_server_det`` next to the mobile recogniser. The sub-models are
   therefore named explicitly -- see :data:`TEXT_DETECTION_MODEL` and
   :data:`RECOGNITION_MODEL_BY_LANG` -- which is what actually delivers the
   small, CPU-friendly pair that decision AD-06 assumes.
"""

TEXT_DETECTION_MODEL: Final[str] = "PP-OCRv5_mobile_det"
"""Text-detection sub-model pinned for CPU inference.

Naming it explicitly is a **performance fix, not a preference**. Passing only
``lang``/``ocr_version`` to :class:`~paddleocr.PaddleOCR` produces a *mixed*
pipeline: Phase 7 observed the engine loading ``PP-OCRv5_server_det`` next to
the mobile recogniser. Measured on the project's i5-14600K, that mistake cost
roughly **10x** on the OCR stage -- pipeline OCR median fell from **1.327,9 ms**
to **133,4 ms** once both sub-models were pinned to mobile -- and it had gone
unnoticed because the class still reported itself as "mobile".

It is the single change that turned NFR-P1 from a 4,4x miss into a 4,4x pass;
the detector backend, which the specification ranked as the first optimisation
to try, was never the bottleneck.
"""

RECOGNITION_MODEL_BY_LANG: Final[dict[str, str]] = {
    "en": "en_PP-OCRv5_mobile_rec",
    "ch": "PP-OCRv5_mobile_rec",
}
"""Recognition sub-model per language code, all mobile variants.

Vietnamese plates carry only Latin letters and digits, so ``en`` is both correct
and faster than a multilingual model. A language absent from this table falls
back to letting PaddleOCR resolve the pair from ``lang``/``ocr_version``, which
keeps an unusual configuration working rather than failing outright.
"""

DEFAULT_ENABLE_MKLDNN: Final[bool] = False
"""Whether the oneDNN (MKL-DNN) CPU acceleration path is enabled by default.

Disabled, because it is **broken on this project's target platform**. With
``paddlepaddle`` 3.3.1 on Windows/CPU, running the PP-OCRv5 detection model
through oneDNN aborts with::

    NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute
    not support [pir::ArrayAttribute<pir::DoubleAttribute>]

The PIR executor cannot translate one of the model's attributes for the oneDNN
kernel. Turning oneDNN off falls back to the plain CPU kernels, which run the
same model correctly at a modest speed cost. Flip this per instance once the
upstream bug is fixed, and re-measure -- it is a pure performance knob, not an
accuracy one.
"""

_WARMUP_HEIGHT: Final[int] = 64
_WARMUP_WIDTH: Final[int] = 224
_MIN_OCR_HEIGHT: Final[int] = 64
"""Crops shorter than this are enlarged before OCR.

Plate crops coming out of the detector are often only 20-40 px tall. Enlarging
before contrast enhancement gives CLAHE more pixels to work on, and keeps the
engine from having to upscale an already degraded input itself.
"""

_MAX_OCR_HEIGHT: Final[int] = 64
"""Crops taller than this are shrunk before OCR.

Equal to :data:`_MIN_OCR_HEIGHT` on purpose: together the two constants say
"normalise the strip to 64 px, whichever side it comes from", which is the only
statement about scale the OCR stage should be making.

Adding the upper bound was a **bug fix**, not tuning. Without it the PP-OCR text
detector receives glyphs hundreds of pixels tall on any close-up crop and
detects nothing whatsoever -- 0 of 100 sampled crops of the Phase 2b label
corpus produced a single character. With it, the same 100 crops read at 48/50
(one-line) and 31/50 (two-line). See the warning on
:func:`~ai.inference.two_line.preprocess_plate`'s ``downscale_to_height``
argument for why the failure stayed hidden for so long.

64 px was chosen from a sweep over 48, 64, 96, 128 and 192 on that corpus: 48
and 64 tie, and accuracy on two-line plates falls away above 64 (23/50 at 96).
It also leaves a modest margin over PP-OCR's own 48 px recognition input, so
the engine never has to upscale.
"""

OCR_INPUT_HEIGHT: Final[int] = _MIN_OCR_HEIGHT
"""Public alias for the height every crop is normalised to before OCR.

Exported so that evaluation harnesses and tests can assert against the same
number the recogniser uses, instead of re-declaring it and drifting.
"""

MIN_FRAGMENT_HEIGHT_RATIO: Final[float] = 0.50
"""Minimum height of a text fragment, relative to the tallest one, to be kept.

Guards against a failure mode observed during Phase 4 bring-up: CLAHE
necessarily amplifies whatever variation exists in a flat region, and where
that region is near-uniform the amplified sensor noise can acquire enough
texture for the text detector to fire on it. On a synthetic plate this produced
a spurious 10 px-tall fragment reading ``"cYanmaGaYGntaYellowb"`` at 0.84
confidence, alongside the two genuine rows at 125 px and 87 px.

A plain confidence threshold does not separate those cases -- 0.84 is a
perfectly ordinary score. Geometry does: after the split-and-merge transform
every legitimate character row occupies, by construction, a large share of the
strip's height, so a fragment far shorter than the tallest one is an artefact
rather than a plate character. Measuring against the tallest *fragment* instead
of the image height keeps the rule insensitive to how tightly the crop was
framed.

Why 0.50 and not the original 0.35
----------------------------------
The halves are cut to **overlap on purpose**, and on a tightly framed crop the
band they share carries the feet of the upper row down into the lower half. The
detector then finds that sliver as a text region of its own, next to the genuine
row. On ``demo/images/nhieu-bien-3.png`` a motorcycle plate reading
``59-F2 / 277.93`` produced::

    '5952'    height=21    <- feet of the upper row, bled through the overlap
    '277.93'  height=51    <- the genuine lower row

21/51 = 0.41, which cleared the old 0.35 threshold. The two were concatenated
into ``277.935952``, and the nine characters that came out of normalisation
happened to match a legal motorcycle layout -- so the plate was reported as
**valid** while being wrong, and the two-line rescue never fired, because the
rescue only retries reads that failed validation. A confidently wrong answer is
strictly worse than a refusal here.

Raised to 0.50 on measurement, not on the strength of that one image: over 400
two-line plates from the labelled corpus, 0.50 against 0.35 gained 10 plates and
lost **none** (54.5% to 57.0%, +2.5 points), with 34 strings changing in total.
See ``docs/reports/15-fragment-height-ab.json``. The gain is larger than the
single-plate anecdote suggests because the bleed-through is a systematic
consequence of the overlap, not an accident of one crop.
"""


class PaddleOcrRecognizer(BaseRecognizer):
    """Read plate characters with PaddleOCR, handling one- and two-line plates.

    The engine is expensive to construct -- it loads several models and
    allocates its own inference session -- so it is built once, lazily, on the
    first call and reused for every crop afterwards. Rebuilding it per image
    would dominate the latency budget (NFR-P1).

    Instances are **not** thread-safe: the underlying PaddleOCR pipeline keeps
    mutable state between calls. Give each worker thread its own instance, or
    serialise access.

    Typical use::

        recognizer = PaddleOcrRecognizer(InferenceConfig.from_env())
        recognizer.warmup()
        recognition = recognizer.recognize(plate_crop)

    Attributes are configured through :class:`~ai.inference.config.InferenceConfig`;
    the recogniser never reads the environment itself.
    """

    def __init__(
        self,
        config: InferenceConfig | None = None,
        *,
        preprocess: bool = True,
        enable_mkldnn: bool = DEFAULT_ENABLE_MKLDNN,
        engine: Any | None = None,
    ) -> None:
        """Prepare the recogniser without loading any model yet.

        Args:
            config: Runtime settings. A default
                :class:`~ai.inference.config.InferenceConfig` is built when
                omitted. Only the OCR-related fields are used
                (:attr:`~ai.inference.config.InferenceConfig.ocr_lang`,
                :attr:`~ai.inference.config.InferenceConfig.ocr_use_gpu`,
                :attr:`~ai.inference.config.InferenceConfig.two_line_aspect_ratio_threshold`).
            preprocess: Whether to run
                :func:`~ai.inference.two_line.preprocess_plate` on each crop.
                Exposed so Phase 7 can measure what the pre-processing chain
                contributes by turning it off.
            enable_mkldnn: Whether to let PaddlePaddle use its oneDNN CPU
                kernels. Defaults to ``False``; see
                :data:`DEFAULT_ENABLE_MKLDNN` for why.
            engine: An already-constructed OCR engine to use instead of
                building one. Intended for tests and for benchmarking two
                configurations without paying the load cost twice. Must expose
                a ``predict(image)`` method compatible with PaddleOCR 3.x.
        """
        self._config = config if config is not None else InferenceConfig()
        self._preprocess = preprocess
        self._enable_mkldnn = enable_mkldnn
        self._engine = engine

    @property
    def name(self) -> str:
        """Return the engine identifier used in logs and benchmark reports.

        The identifier names the **detection** sub-model as well as the
        generation, because those are separate choices: before Phase 7 this
        property reported ``-mobile`` while the engine was in fact running a
        server-sized detector, and every benchmark number published under that
        name was mislabelled. Naming what is actually loaded is what stops that
        from recurring.
        """
        recognition = RECOGNITION_MODEL_BY_LANG.get(self._config.ocr_lang)
        if recognition is None:
            return f"paddleocr-{OCR_VERSION}-auto({self._config.ocr_lang})"
        return f"paddleocr-{OCR_VERSION}-mobile(det={TEXT_DETECTION_MODEL})"

    @property
    def config(self) -> InferenceConfig:
        """Return the configuration this recogniser was built with."""
        return self._config

    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        """Read the plate text from a cropped plate image.

        Pipeline applied to the crop:

        1. Estimate the number of text lines from the aspect ratio.
        2. If two, split into overlapping halves and re-stack them horizontally
           into a single-line strip (see :mod:`ai.inference.two_line`).
        3. Enhance contrast and denoise, unless disabled.
        4. Run OCR and concatenate the recognised fragments left to right.

        Deskewing is deliberately **not** part of this method. It was measured
        as an always-on first step here and it *lost* ground: on the demo
        video's detector-produced crops it converted two good reads into junk
        for zero recoveries, because a mis-fitted rectangle on a small blurred
        crop cuts characters away. Skew recovery therefore lives in the
        pipeline's failure-retry ladder
        (:func:`~ai.inference.pipeline.retry_skewed_variants`), where it runs
        only on reads that have already failed and keeps its result only when
        the re-read validates -- an attempt that can win but never lose.

        The returned :attr:`~ai.inference.types.PlateRecognition.text` is
        **not** normalised -- it is the raw engine output with whitespace
        removed and letters upper-cased. Character correction, separator
        stripping and format validation belong to the normalizer, which is why
        :attr:`~ai.inference.types.PlateRecognition.is_valid_format` is always
        ``False`` here: this stage has no authority to judge the format.

        Args:
            plate_image: The cropped plate as a BGR ``uint8`` array. This is
                the region delimited by a detected bounding box, not the whole
                scene.

        Returns:
            A :class:`~ai.inference.types.PlateRecognition`. When the engine
            reads nothing -- a blurred, occluded or over-exposed crop -- the
            result carries empty text and ``0.0`` confidence instead of an
            exception. An unreadable plate is a normal outcome that must still
            be recorded and counted.

        Raises:
            InvalidImageError: If the crop is empty or not a valid image.
            ModelLoadError: If the OCR models cannot be loaded.
            RecognitionError: If the engine itself fails during inference.
        """
        self._validate_crop(plate_image)

        started = time.perf_counter()
        line_count = estimate_line_count(plate_image, self._config.two_line_aspect_ratio_threshold)

        ocr_input = plate_image
        if line_count == 2:
            upper, lower = split_two_line(ocr_input)
            ocr_input = merge_two_line(upper, lower)

        if self._preprocess:
            ocr_input = preprocess_plate(
                ocr_input,
                upscale_to_height=_MIN_OCR_HEIGHT,
                downscale_to_height=_MAX_OCR_HEIGHT,
            )
        else:
            # The scale cap is a correctness requirement of the engine, not part
            # of the enhancement chain, so disabling pre-processing for an
            # ablation must not disable it -- otherwise the ablation measures
            # the detector failing to fire rather than what CLAHE contributes.
            ocr_input = preprocess_plate(
                ocr_input,
                to_grayscale=False,
                apply_clahe=False,
                denoise=False,
                upscale_to_height=_MIN_OCR_HEIGHT,
                downscale_to_height=_MAX_OCR_HEIGHT,
            )

        texts, scores = self._run_ocr(ocr_input)
        raw_text = " ".join(texts).strip()
        text = "".join(raw_text.split()).upper()
        confidence = _aggregate_confidence(texts, scores)

        # Where the serial ends on a two-line plate. The halves were stacked
        # side by side above, so the engine returns one fragment per half and
        # the first fragment IS the upper line -- `67C` (three characters, one
        # letter of serial) versus `77H5` (four, two characters of serial).
        # That distinction is invisible in the flat string and decides whether
        # the number is grouped as five digits or four.
        #
        # Stays 0 when the engine returned a single fragment, which means the
        # upper line was not read: absent evidence, not wrong evidence.
        upper_char_count = 0
        if line_count == 2 and len(texts) >= 2:
            upper_char_count = sum(1 for ch in texts[0] if ch.isalnum())

        _LOGGER.info(
            "Plate recognition finished",
            extra={
                "engine": self.name,
                "line_count": line_count,
                "raw_text": raw_text,
                "text": text,
                "confidence": round(confidence, 4),
                "segments": len(texts),
                "upper_char_count": upper_char_count,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )

        return PlateRecognition(
            text=text,
            raw_text=raw_text,
            confidence=confidence,
            line_count=line_count,
            is_valid_format=False,
            upper_char_count=upper_char_count,
        )

    def warmup(self) -> None:
        """Load the models and run one throwaway pass to prime the engine.

        The first inference in a process is several times slower than the rest
        because weights are paged in and lazy kernels are compiled. Calling
        this at start-up moves that cost off the first user request.

        Failures are logged and swallowed rather than raised: a warm-up is an
        optimisation, and refusing to start the service because a synthetic
        blank image produced no text would be the wrong trade-off. A genuine
        model-loading problem surfaces on the first real call.
        """
        try:
            blank = np.full((_WARMUP_HEIGHT, _WARMUP_WIDTH, 3), 255, dtype=np.uint8)
            started = time.perf_counter()
            self.recognize(blank)
            _LOGGER.info(
                "OCR engine warmed up",
                extra={
                    "engine": self.name,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
                },
            )
        except Exception as error:  # noqa: BLE001 - warm-up must never block start-up
            _LOGGER.warning(
                "OCR warm-up failed, continuing without it",
                extra={"engine": self.name, "error": str(error)},
            )

    def _run_ocr(self, image: ImageArray) -> tuple[list[str], list[float]]:
        """Run the engine and return the fragments in left-to-right order.

        Args:
            image: The prepared single-line strip.

        Returns:
            A ``(texts, scores)`` pair of equal length, ordered by horizontal
            position. Both are empty when nothing was read.

        Raises:
            ModelLoadError: If the engine cannot be constructed.
            RecognitionError: If inference fails.
        """
        engine = self._ensure_engine()
        try:
            raw_results = engine.predict(image)
        except Exception as error:
            raise RecognitionError(
                f"PaddleOCR inference failed on a {image.shape} crop: {error}"
            ) from error

        return _parse_ocr_output(raw_results)

    def _ensure_engine(self) -> Any:
        """Return the OCR engine, constructing it on first use.

        Returns:
            The PaddleOCR pipeline object.

        Raises:
            ModelLoadError: If PaddleOCR is not installed or its models cannot
                be loaded -- typically a missing package, or no network access
                on the first run when the weights still have to be downloaded.
        """
        if self._engine is not None:
            return self._engine

        try:
            from paddleocr import PaddleOCR, TextRecognition
        except ImportError as error:
            raise ModelLoadError(
                "PaddleOCR is not installed in the active environment; "
                "install the OCR requirements before running recognition"
            ) from error

        device = "gpu" if self._config.ocr_use_gpu else "cpu"

        if self._config.ocr_skip_detection:
            return self._build_recognition_only_engine(TextRecognition, device)

        # Both sub-model names are pinned together, or neither is. Supplying
        # only one makes PaddleOCR ignore lang/ocr_version for the other and
        # fall back to its own default -- in that state it silently selected
        # PP-OCRv6_medium_rec, a different model generation entirely.
        recognition_model = RECOGNITION_MODEL_BY_LANG.get(self._config.ocr_lang)
        if recognition_model is not None:
            model_kwargs: dict[str, Any] = {
                "text_detection_model_name": TEXT_DETECTION_MODEL,
                "text_recognition_model_name": recognition_model,
            }
            selection = f"det={TEXT_DETECTION_MODEL}, rec={recognition_model}"
            rec_dir = self._config.ocr_rec_model_dir
            if (
                rec_dir is not None
                and rec_dir.is_dir()
                and (rec_dir / "inference.pdiparams").exists()
            ):
                # A fine-tuned recognition model (ai/training). The model NAME
                # stays pinned so PaddleOCR resolves the right architecture and
                # pre/post-processing; the DIR overrides where the weights and
                # the exported dictionary come from.
                model_kwargs["text_recognition_model_dir"] = str(rec_dir)
                selection += f", rec_dir={rec_dir}"



        else:
            LOGGER_MSG = (
                "No pinned mobile model pair for lang=%r; falling back to "
                "PaddleOCR's own resolution, which may select a server-sized "
                "detection model and cost roughly 2,7x more per crop."
            )
            _LOGGER.warning(LOGGER_MSG, self._config.ocr_lang)
            model_kwargs = {
                "lang": self._config.ocr_lang,
                "ocr_version": OCR_VERSION,
            }
            selection = f"lang={self._config.ocr_lang}, {OCR_VERSION}"

        if device == "cpu":
            model_kwargs["cpu_threads"] = int(os.environ.get("OMP_NUM_THREADS", "1"))

        started = time.perf_counter()
        try:
            self._engine = PaddleOCR(
                device=device,
                enable_mkldnn=self._enable_mkldnn,
                # A plate crop contains a single text region, so the
                # document-level pre-processing stages cost latency for little
                # return here.
                #
                # This comment used to add "and is already deskewed by the
                # detector", which is false: a YOLO box is axis-aligned and
                # deskews nothing. A plate photographed from the kerb arrives
                # tilted, and the tilt survives cropping. The consequence is
                # measurable -- on frame 168 of ``demo/demo-video.mp4`` a
                # legible ``77-H5 / 4374`` yields a 146x42 box, aspect ratio
                # 3.48, so :func:`~ai.inference.two_line.estimate_line_count`
                # calls a two-line plate one-line and OCR returns nothing.
                # Forcing the two-line path does not rescue it either, because a
                # horizontal cut crosses both rows diagonally.
                #
                # The project's own decision log describes the two-line pipeline
                # as "rectify -> classify -> split -> hstack -> OCR". The
                # rectify stage does not exist in this codebase. Turning these
                # flags on is not the fix -- they unwarp documents, not plates --
                # but the missing stage should not hide behind a false claim
                # that something else already did the work.
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                **model_kwargs,
            )
        except Exception as error:
            raise ModelLoadError(
                f"Failed to load PaddleOCR ({selection}, device={device!r}): {error}"
            ) from error

        _LOGGER.info(
            "OCR engine loaded",
            extra={
                "engine": self.name,
                "lang": self._config.ocr_lang,
                "device": device,
                "enable_mkldnn": self._enable_mkldnn,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )
        return self._engine

    def _build_recognition_only_engine(self, factory: Any, device: str) -> Any:
        """Build a recognition-only engine that reads the whole crop at once.

        The crop handed to this class has already been localised by the
        detector, aspect-repaired, and -- when two-line -- split and re-stacked
        into one horizontal strip. It is a single text line, so PaddleOCR's
        text-detection stage has nothing left to find; all it does is cut the
        strip into fragments that then have to be stitched back together.

        See :attr:`~ai.inference.config.InferenceConfig.ocr_skip_detection` for
        the measurement that put this on by default.

        Args:
            factory: The ``paddleocr.TextRecognition`` class.
            device: ``"cpu"`` or ``"gpu"``.

        Returns:
            The recognition module, which exposes the same ``predict(image)``
            call as the full pipeline.

        Raises:
            ModelLoadError: If the recognition model cannot be loaded.
        """
        recognition_model = RECOGNITION_MODEL_BY_LANG.get(self._config.ocr_lang)
        kwargs: dict[str, Any] = {"device": device}
        if device == "cpu":
            kwargs["cpu_threads"] = int(os.environ.get("OMP_NUM_THREADS", "1"))
        if recognition_model is not None:
            kwargs["model_name"] = recognition_model

        rec_dir = self._config.ocr_rec_model_dir
        if rec_dir is not None and rec_dir.is_dir() and (rec_dir / "inference.pdiparams").exists():
            kwargs["model_dir"] = str(rec_dir)

        started = time.perf_counter()
        try:
            self._engine = factory(**kwargs)
        except Exception as error:
            raise ModelLoadError(
                f"Failed to load the recognition-only engine ({kwargs}): {error}"
            ) from error

        _LOGGER.info(
            "OCR engine loaded (recognition only, detection stage skipped)",
            extra={
                "engine": self.name,
                "model_name": recognition_model,
                "model_dir": str(rec_dir) if "model_dir" in kwargs else None,
                "device": device,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )
        return self._engine

    @staticmethod
    def _validate_crop(plate_image: ImageArray) -> None:
        """Reject crops that cannot be processed.

        Args:
            plate_image: Candidate crop.

        Raises:
            InvalidImageError: If the array is ``None``, not a NumPy array, has
                the wrong rank, or has a zero-sized side.
        """
        if plate_image is None or not isinstance(plate_image, np.ndarray):
            raise InvalidImageError(
                "plate_image must be a NumPy array, got " f"{type(plate_image).__name__}"
            )
        if plate_image.ndim not in (2, 3):
            raise InvalidImageError(
                "plate_image must be a 2-D or 3-D array, got " f"{plate_image.ndim} dimensions"
            )
        if plate_image.size == 0 or 0 in plate_image.shape[:2]:
            raise InvalidImageError(
                "plate_image must have a positive width and height, got shape "
                f"{plate_image.shape}"
            )


def _aggregate_confidence(texts: Sequence[str], scores: Sequence[float]) -> float:
    """Combine per-fragment OCR scores into one confidence for the plate.

    The mean is weighted by fragment length. A plain average would let a
    one-character fragment recognised with 0.99 confidence mask a seven-
    character fragment recognised with 0.40 -- and on a plate it is the long
    fragment that carries the identity.

    Args:
        texts: Recognised fragments.
        scores: Their confidences, aligned with ``texts``.

    Returns:
        A confidence in ``[0.0, 1.0]``, or ``0.0`` when nothing was read.
    """
    weights = [len(text) for text in texts]
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    weighted = sum(score * weight for score, weight in zip(scores, weights))
    return float(min(1.0, max(0.0, weighted / total_weight)))


def _parse_ocr_output(raw_results: Any) -> tuple[list[str], list[float]]:
    """Extract texts, scores and reading order from a PaddleOCR result.

    Kept as a free function, and deliberately defensive, because the shape of
    this payload changed between PaddleOCR 2.x and 3.x and may change again.
    Isolating the parsing here means a future upgrade touches one function
    instead of the recognition flow.

    Fragments far shorter than the tallest one are dropped as detector
    artefacts; see :data:`MIN_FRAGMENT_HEIGHT_RATIO`.

    Args:
        raw_results: Whatever ``PaddleOCR.predict`` returned. Expected to be an
            iterable of mapping-like results carrying ``rec_texts``,
            ``rec_scores`` and one of ``rec_polys``/``dt_polys``.

    Returns:
        A ``(texts, scores)`` pair of equal length, sorted by the left edge of
        each fragment so that the plate reads left to right. Empty when the
        payload carries no recognised text.
    """
    if not raw_results:
        return [], []

    # (left edge, height, text, score) -- height only used for artefact filtering.
    fragments: list[tuple[float, float, str, float]] = []
    for result in raw_results:
        texts = _lookup(result, "rec_texts") or []
        scores = _lookup(result, "rec_scores") or []

        if not texts:
            # Recognition-only mode (``ocr_skip_detection``). ``TextRecognition``
            # reads the whole strip in one pass, so it reports a single
            # ``rec_text``/``rec_score`` rather than the pipeline's plural
            # fields, and no polygons at all. Everything downstream already
            # copes with absent geometry, so the singular payload only has to be
            # widened into a one-element list here.
            single = _lookup(result, "rec_text")
            if single:
                texts = [single]
                score = _lookup(result, "rec_score")
                scores = [score] if score is not None else []

        polys = _lookup(result, "rec_polys")
        if polys is None:
            polys = _lookup(result, "dt_polys")

        for index, text in enumerate(texts):
            if not text:
                continue
            score = float(scores[index]) if index < len(scores) else 0.0
            left, height = _fragment_geometry(polys, index)
            fragments.append((left, height, str(text), score))

    fragments = _drop_short_fragments(fragments)
    fragments.sort(key=lambda fragment: fragment[0])
    return (
        [text for _, _, text, _ in fragments],
        [score for _, _, _, score in fragments],
    )


def _drop_short_fragments(
    fragments: list[tuple[float, float, str, float]],
) -> list[tuple[float, float, str, float]]:
    """Discard fragments far shorter than the tallest one.

    Args:
        fragments: ``(left, height, text, score)`` tuples.

    Returns:
        The surviving fragments, in input order. Returned unchanged when no
        fragment reported usable geometry, so the filter can never remove
        everything on a payload it cannot measure.
    """
    tallest = max((height for _, height, _, _ in fragments), default=0.0)
    if tallest <= 0.0:
        return fragments

    minimum = tallest * MIN_FRAGMENT_HEIGHT_RATIO
    kept = [fragment for fragment in fragments if fragment[1] >= minimum]
    dropped = len(fragments) - len(kept)
    if dropped:
        _LOGGER.debug(
            "Discarded short OCR fragments as detector artefacts",
            extra={
                "dropped": dropped,
                "tallest_fragment_height": round(tallest, 1),
                "min_height": round(minimum, 1),
                "dropped_texts": [text for _, height, text, _ in fragments if height < minimum],
            },
        )
    return kept


def _lookup(result: Any, key: str) -> Any:
    """Read ``key`` from a mapping-like or attribute-like OCR result.

    Args:
        result: One entry of the engine's output.
        key: Field name to read.

    Returns:
        The value, or ``None`` when the field is absent.
    """
    try:
        return result[key]
    except (TypeError, KeyError, IndexError):
        return getattr(result, key, None)


def _fragment_geometry(polys: Any, index: int) -> tuple[float, float]:
    """Return the left edge and the height of one detected text polygon.

    Args:
        polys: Sequence of polygons aligned with the recognised fragments, or
            ``None`` when the engine did not report any.
        index: Position of the fragment.

    Returns:
        A ``(left, height)`` pair in pixels. When no geometry is available the
        left edge falls back to ``index`` -- which preserves the engine's own
        ordering -- and the height to ``0.0``, which disables the artefact
        filter rather than letting it act on a guess.
    """
    if polys is None or index >= len(polys):
        return float(index), 0.0
    try:
        polygon = np.asarray(polys[index], dtype=float)
        ys = polygon[:, 1]
        return float(polygon[:, 0].min()), float(ys.max() - ys.min())
    except (ValueError, IndexError, TypeError):
        return float(index), 0.0
