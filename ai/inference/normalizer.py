"""Post-processing stage: position-based correction and validation for Vietnamese license plates (NFR-M1).

Applies positional character repair according to national standards TT 79/2024 and QCVN 08:2024.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Final

from ai.inference.interfaces import BaseNormalizer
from ai.inference.plate_rules import (
    CIVIL_KINDS,
    PATTERNS_BY_KIND,
    PlateKind,
    apply_position_rules,
    clean_text,
    mask_for_length,
)

__all__ = ["KindDecision", "NormalizationOutcome", "VietnamesePlateNormalizer"]

logger = logging.getLogger(__name__)

_FIVE_DIGIT_DOT_GROUP_RE: Final[re.Pattern[str]] = re.compile(r"\d{3}[.,]\d{2}(?!\d)")
"""A ``DDD.DD`` group in the RAW OCR string -- physical proof of a 5-digit number."""

_MIN_PLATE_LENGTH = 7
_MAX_PLATE_LENGTH = 9

_AMBIGUOUS_PAIRS: tuple[frozenset[PlateKind], ...] = (
    # 8 characters: `29B11234` reads as car (29 + B + 11234) or as an old
    # motorcycle (29 + B + 1 + 1234). Section 8.6, ambiguity 1.
    frozenset({PlateKind.CAR, PlateKind.MOTORCYCLE_OLD}),
    # 9 characters: `29LD12345` reads as a special code or as a new-style
    # motorcycle serial. Section 8.6, ambiguity 2.
    frozenset({PlateKind.SPECIAL, PlateKind.MOTORCYCLE_NEW}),
)


@dataclass(frozen=True, slots=True)
class KindDecision:
    """The outcome of classifying a cleaned plate string."""

    kind: PlateKind
    candidates: tuple[PlateKind, ...] = ()
    is_ambiguous: bool = False
    resolved_by_line_count: bool = False


@dataclass(frozen=True, slots=True)
class NormalizationOutcome:
    """Everything the normalizer learned about one OCR string."""

    raw_text: str
    cleaned_text: str
    text: str
    is_valid_format: bool
    decision: KindDecision
    corrections: tuple[tuple[int, str, str], ...] = ()

    @property
    def was_corrected(self) -> bool:
        """Return ``True`` if positional repair changed at least one character."""
        return bool(self.corrections)


class VietnamesePlateNormalizer(BaseNormalizer):
    """Correct and validate Vietnamese plate strings coming out of OCR."""

    def normalize(self, raw_text: str) -> tuple[str, bool]:
        """Correct a raw OCR string and check it against the plate formats."""
        outcome = self.normalize_detailed(raw_text)
        return outcome.text, outcome.is_valid_format

    def normalize_detailed(
        self, raw_text: str, line_count: int | None = None
    ) -> NormalizationOutcome:
        """Run the full normalisation and report everything that happened.

        Args:
            raw_text: The unmodified OCR output.
            line_count: Number of text lines on the physical plate, ``1`` or
                ``2``, when the caller knows it. The upper layer derives it
                from the crop's aspect ratio. It is used solely to resolve the
                8-character car / old-motorcycle ambiguity; see
                :meth:`detect_plate_kind` for what it can and cannot settle.
                ``None`` means "unknown", which is always safe.

        Returns:
            A :class:`NormalizationOutcome`. It is never ``None`` and never
            raises for malformed input: an empty or nonsensical string simply
            comes back with ``is_valid_format=False``.
        """
        cleaned = clean_text(raw_text)

        if not cleaned:
            logger.debug(
                "Plate normalisation received no usable characters",
                extra={"raw_text": raw_text},
            )
            return NormalizationOutcome(
                raw_text=raw_text,
                cleaned_text="",
                text="",
                is_valid_format=False,
                decision=KindDecision(kind=PlateKind.UNKNOWN),
            )

        # Rule 1: a string that is already valid must not be touched.
        decision = self.detect_plate_kind(cleaned, line_count=line_count, raw_text=raw_text)
        if decision.kind in CIVIL_KINDS:
            return NormalizationOutcome(
                raw_text=raw_text,
                cleaned_text=cleaned,
                text=cleaned,
                is_valid_format=True,
                decision=decision,
            )

        # Rule 1b: Military plates return unrepaired and marked invalid as civil format
        if decision.kind is PlateKind.MILITARY:
            return NormalizationOutcome(
                raw_text=raw_text,
                cleaned_text=cleaned,
                text=cleaned,
                is_valid_format=False,
                decision=decision,
            )

        mask = mask_for_length(len(cleaned))
        if mask is None:
            logger.debug(
                "Plate string length outside the repairable range",
                extra={
                    "raw_text": raw_text,
                    "cleaned_text": cleaned,
                    "length": len(cleaned),
                    "expected_range": (_MIN_PLATE_LENGTH, _MAX_PLATE_LENGTH),
                },
            )
            return NormalizationOutcome(
                raw_text=raw_text,
                cleaned_text=cleaned,
                text=cleaned,
                is_valid_format=False,
                decision=decision,
            )

        repaired = apply_position_rules(cleaned, mask)
        corrections = tuple(
            (index, before, after)
            for index, (before, after) in enumerate(zip(cleaned, repaired, strict=True))
            if before != after
        )
        repaired_decision = self.detect_plate_kind(
            repaired, line_count=line_count, raw_text=raw_text
        )
        is_valid = repaired_decision.kind in CIVIL_KINDS

        if corrections:
            logger.info(
                "Applied positional OCR repair to plate string",
                extra={
                    "raw_text": raw_text,
                    "cleaned_text": cleaned,
                    "normalized_text": repaired,
                    "mask": mask,
                    "corrections": corrections,
                    "is_valid_format": is_valid,
                },
            )
        if not is_valid:
            logger.debug(
                "Plate string could not be repaired into a known format",
                extra={
                    "raw_text": raw_text,
                    "normalized_text": repaired,
                    "mask": mask,
                },
            )

        return NormalizationOutcome(
            raw_text=raw_text,
            cleaned_text=cleaned,
            text=repaired,
            is_valid_format=is_valid,
            decision=repaired_decision,
            corrections=corrections,
        )

    def detect_plate_kind(
        self,
        text: str,
        line_count: int | None = None,
        raw_text: str | None = None,
    ) -> KindDecision:
        """Classify a cleaned plate string.

        Patterns are tried in the priority order of
        :data:`~ai.inference.plate_rules.PATTERNS_BY_KIND`, and *all* matches
        are collected, because two ambiguities are documented and verified:

        ================= ============= ==============================
        Ambiguity         Example       Resolvable by
        ================= ============= ==============================
        car / old moto    ``29B11234``  line count / printed dot
        special / new mot ``29LD12345`` not by line count
        ================= ============= ==============================

        **What ``line_count`` can settle.** Motorcycles are always two-line
        plates, so ``line_count=1`` proves the string is a car plate and the
        ambiguity disappears. ``line_count=2`` proves nothing on its own: a
        short car plate is two-line too, so the pair stays ambiguous and the
        flag remains set. Claiming otherwise would fabricate information the
        input does not contain.

        **What the raw string can settle.** The physical plate prints a
        five-digit order number with a dot (``609.69``) and a four-digit one
        without. When the RAW OCR string carries a ``DDD.DD`` group, the
        number has five digits, so the serial has one letter -- a car -- and
        the ambiguity is genuinely gone. This is the evidence that puts the
        two-line car plates the prior used to mislabel (``51H-609.69`` on an
        SUV tailgate, ``51C-920.87`` on a truck) into the right family
        without costing the measured 450/452 motorcycle majority anything:
        their four-digit numbers never print a dot.

        Args:
            text: A cleaned string (digits and upper-case letters only).
            line_count: ``1`` or ``2`` when known, otherwise ``None``. Any
                other value is ignored.
            raw_text: The unmodified OCR output, separators included, when the
                caller has it. Used solely for the printed-dot evidence.

        Returns:
            A :class:`KindDecision` carrying the best candidate, every
            candidate, and whether the result is ambiguous.
        """
        candidates = tuple(
            kind for kind, pattern in PATTERNS_BY_KIND.items() if pattern.match(text)
        )
        if not candidates:
            return KindDecision(kind=PlateKind.UNKNOWN)

        candidate_set = set(candidates)
        is_ambiguous = any(pair <= candidate_set for pair in _AMBIGUOUS_PAIRS)
        # Default initialization before branching to avoid UnboundLocalError
        best = candidates[0]
        resolved = False

        car_or_old_moto = {PlateKind.CAR, PlateKind.MOTORCYCLE_OLD} <= candidate_set
        printed_dot = bool(raw_text and _FIVE_DIGIT_DOT_GROUP_RE.search(raw_text))
        car_truck_van_serial = bool(re.match(r"^\d{2}[CDHF]\d{5}$", text))

        if is_ambiguous and car_or_old_moto and (
            line_count == 1 or printed_dot or car_truck_van_serial
        ):
            # Single-line, printed dot, or commercial series resolves ambiguity to CAR
            best = PlateKind.CAR

            is_ambiguous = any(
                pair <= candidate_set - {PlateKind.MOTORCYCLE_OLD} for pair in _AMBIGUOUS_PAIRS
            )
            resolved = True
        elif is_ambiguous and line_count == 2 and car_or_old_moto:

            # Prior preference for 2-line ambiguous plates resolves to MOTORCYCLE_OLD
            best = PlateKind.MOTORCYCLE_OLD
            resolved = True

        return KindDecision(
            kind=best,
            candidates=candidates,
            is_ambiguous=is_ambiguous,
            resolved_by_line_count=resolved,
        )

    def is_valid_format(self, text: str, line_count: int | None = None) -> bool:
        """Return whether a cleaned string matches a known civil plate format.

        Army plates are excluded on purpose: they match
        :data:`~ai.inference.plate_rules.RE_MILITARY`, but that pattern exists
        to *identify and exclude* them, not to bless them as valid civil
        registrations.

        Args:
            text: A cleaned string. Raw strings should be passed through
                :func:`~ai.inference.plate_rules.clean_text` first.
            line_count: ``1`` or ``2`` when known.

        Returns:
            ``True`` if any civil pattern matches.
        """
        return self.detect_plate_kind(text, line_count=line_count).kind in CIVIL_KINDS

    def format_for_display(
        self,
        text: str,
        line_count: int | None = None,
        kind: PlateKind | str | None = None,
        upper_char_count: int = 0,
    ) -> str:
        """Re-insert separators so a plate reads naturally in the UI.

        The canonical stored form is separator-free (section 7.5); separators
        are a presentation concern and are added back only here. The full
        grouping rule table, one row per plate family, is documented in
        ``docs/reports/23-display-format-rules.md`` -- this method is its
        implementation and must not drift from it.

        Layout produced: serial group, ``-``, then the order number with a dot
        before its last two digits when it has five::

            30A12345  -> 30A-123.45
            29A1234   -> 29A-1234
            29AA12345 -> 29AA-123.45
            80001NG01 -> 80-001-NG-01

        A single-line rendering is used throughout for consistency; the source
        document also shows a two-line layout for motorcycles (``29-AA`` above
        ``123.45``), which is a rendering decision for the front end rather
        than a property of the plate string.

        Args:
            text: A cleaned, normalised plate string.
            line_count: ``1`` or ``2`` when known, forwarded to classification
                when ``kind`` is not supplied.
            kind: The family the caller has ALREADY established for this
                string (a :class:`~ai.inference.plate_rules.PlateKind` or its
                string value). When given and consistent with the string, the
                grouping follows it instead of re-deriving -- this is what
                keeps the family badge and the digit grouping telling the same
                story: ``51H60969`` classified as a car by the printed-dot
                evidence must render ``51H-609.69``, never ``51H6-0969``.
            upper_char_count: For a two-line plate, how many characters the
                engine read from the **upper** line (see
                :attr:`~ai.inference.types.PlateRecognition.upper_char_count`).
                ``0`` means unknown.

                When it is known it **outranks** ``kind``, because it is direct
                evidence from the image rather than an inference from the
                string. An eight-character two-line plate is genuinely
                ambiguous otherwise: ``67C10815`` groups as ``67C-108.15`` if
                the upper line read ``67C`` and as ``67C1-0815`` if it read
                ``67C1``, and both are legal. Measured on the demo set, the
                family-derived grouping got five of seven such plates right and
                two wrong; the upper line gets all seven right.

                Ignored unless the implied split leaves a 4- or 5-digit number,
                so a mis-read fragment length cannot produce a grouping the
                plate rules do not allow.

        Returns:
            The formatted string, or ``text`` unchanged when it matches no
            known pattern -- an unrecognised string is shown exactly as read,
            never dressed up to look valid.
        """
        resolved_kind: PlateKind | None = None
        if kind is not None:
            try:
                resolved_kind = kind if isinstance(kind, PlateKind) else PlateKind(kind)
            except ValueError:
                resolved_kind = None
            if resolved_kind in (PlateKind.UNKNOWN, None):
                resolved_kind = None
            elif PATTERNS_BY_KIND[resolved_kind].match(text) is None:
                # Fall back to deriving when caller's kind does not match string regex
                resolved_kind = None

        if resolved_kind is None:
            decision = self.detect_plate_kind(text, line_count=line_count)
            resolved_kind = decision.kind
        if resolved_kind is PlateKind.UNKNOWN:
            return text

        match = PATTERNS_BY_KIND[resolved_kind].match(text)
        if match is None:  # pragma: no cover - guarded by detect_plate_kind
            return text
        groups = match.groupdict()

        if resolved_kind is PlateKind.DIPLOMATIC:
            return (
                f"{groups['province']}-{groups['country']}-" f"{groups['code']}-{groups['number']}"
            )
        if resolved_kind is PlateKind.MILITARY:
            return f"{groups['unit']}-{groups['number']}"

        number = groups["number"]
        prefix = text[: len(text) - len(number)]

        # Upper line char count indicates where serial ends for 2-line civil plates
        if (
            upper_char_count > 0
            and line_count == 2
            and resolved_kind in _UPPER_LINE_ADJUSTABLE_KINDS
            and upper_char_count != len(prefix)
            and len(text) - upper_char_count in (4, 5)
            and text[:upper_char_count].isalnum()
        ):
            prefix = text[:upper_char_count]
            number = text[upper_char_count:]

        return f"{prefix}-{_group_number(number)}"


_UPPER_LINE_ADJUSTABLE_KINDS: Final[frozenset[PlateKind]] = frozenset(
    {
        PlateKind.CAR,
        PlateKind.MOTORCYCLE_OLD,
        PlateKind.MOTORCYCLE_NEW,
        PlateKind.BLUE_CAR,
        PlateKind.BLUE_MOTORCYCLE,
    }
)
"""Families whose grouping is `serial-number` and therefore movable.

Diplomatic and military plates are excluded on purpose: their layouts are not
`serial` + `number` at all (``80-001-NG-01``, ``KV-6938``), so a character
count taken from the upper line has nothing to move there. Restricting the
adjustment to civil families keeps it from reformatting a layout it does not
model.
"""


def _group_number(number: str) -> str:
    """Insert the thousands dot into a plate's order-number group.

    Args:
        number: The order number, 4 or 5 digits.

    Returns:
        ``"123.45"`` for five digits, ``"1234"`` unchanged for four. Four-digit
        plates carry no dot on the physical plate (section 2.3).
    """
    if len(number) == 5:
        return f"{number[:3]}.{number[3:]}"
    return number
