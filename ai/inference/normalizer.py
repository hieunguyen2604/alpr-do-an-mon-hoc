"""Post-processing stage: correct and validate raw OCR output.

This module implements :class:`~ai.inference.interfaces.BaseNormalizer` for
Vietnamese plates. It is the project's own technical contribution: the
detector and the recogniser are off-the-shelf models, whereas the rules applied
here come from the national plate standard and are what turns an approximate
character string into a plate number that can be trusted.

The central idea (section 9.1 of ``docs/reports/01-vn-plate-standards.md``) is
that **repair must be positional, never global**. A global table such as
``{"O": "0", "I": "1"}`` applied to the whole string destroys correct data. The
standard, however, tells us in advance whether each position *must* be a digit
or *must* be a letter, and that constraint is free information: at a digit
position every letter read is by definition a mistake, and vice versa.

Processing order, mirroring the flowchart of section 9.5::

    raw OCR string
      -> clean (fold Đ, upper-case, strip separators)
      -> already matches a pattern?  yes -> valid, return untouched
      -> length within 7..9?         no  -> controlled failure, still returned
      -> apply the position mask (skipping the wildcard)
      -> matches now?                yes -> valid, corrections logged
                                     no  -> controlled failure, still returned

Three operating rules are load-bearing:

1. **Try the regex before repairing.** If the string is already valid, any edit
   can only damage it.
2. **Never discard.** An unrepairable string is returned with
   ``is_valid_format=False`` and stored by the caller. Dropping it would hide
   recognition failures from the statistics and remove the error-analysis
   material the evaluation chapter depends on.
3. **Keep the raw string.** The caller persists it in ``raw_ocr_text``.
   Comparing raw against normalised is the only way to measure what this stage
   contributes -- which is exactly why it lives outside the recogniser.

The module depends on the standard library only; it imports no web framework
and no schema library (NFR-M1).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

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
    """The outcome of classifying a cleaned plate string.

    Classification returns a *set* of candidates rather than one answer,
    because two documented ambiguities are not resolvable from the characters
    alone (section 8.6).

    Attributes:
        kind: The best candidate under the priority order of
            :data:`~ai.inference.plate_rules.PATTERNS_BY_KIND`, or
            :attr:`~ai.inference.plate_rules.PlateKind.UNKNOWN` if nothing
            matched.
        candidates: Every kind whose pattern matched, in priority order.
        is_ambiguous: ``True`` when the candidates include one of the two
            documented ambiguous pairs *and* the ambiguity was not resolved by
            the supplied line count.
        resolved_by_line_count: ``True`` when a line count was supplied and it
            settled an otherwise ambiguous string.
    """

    kind: PlateKind
    candidates: tuple[PlateKind, ...] = ()
    is_ambiguous: bool = False
    resolved_by_line_count: bool = False


@dataclass(frozen=True, slots=True)
class NormalizationOutcome:
    """Everything the normalizer learned about one OCR string.

    :meth:`VietnamesePlateNormalizer.normalize` narrows this down to the
    ``(text, is_valid_format)`` pair required by the interface; callers that
    want the classification, the ambiguity flag or the list of applied
    corrections use :meth:`VietnamesePlateNormalizer.normalize_detailed`
    instead.

    Attributes:
        raw_text: The string exactly as the OCR engine returned it.
        cleaned_text: The string after separator stripping and upper-casing,
            before any positional repair.
        text: The final normalised string. Equals :attr:`cleaned_text` when no
            repair was applied or when repair was impossible.
        is_valid_format: Whether :attr:`text` matches a known civil plate
            pattern. Army plates match :data:`RE_MILITARY` but are reported as
            ``False`` here: they are recognised in order to be excluded.
        decision: The classification of :attr:`text`.
        corrections: One ``(index, before, after)`` entry per character the
            positional rules changed, in order. Empty when nothing was
            repaired. This is the audit trail for the evaluation chapter.
    """

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
    """Correct and validate Vietnamese plate strings coming out of OCR.

    The class is stateless and therefore safe to share across threads and
    reuse for the lifetime of the process; a single instance is normally built
    at start-up and injected into the pipeline.

    Example:
        >>> normalizer = VietnamesePlateNormalizer()
        >>> normalizer.normalize("3OA-123.45")
        ('30A12345', True)
        >>> normalizer.normalize("30012345")
        ('30D12345', True)
        >>> normalizer.normalize("3OB12E45")
        ('30B12E45', False)
    """

    def normalize(self, raw_text: str) -> tuple[str, bool]:
        """Correct a raw OCR string and check it against the plate formats.

        This is the interface method of
        :class:`~ai.inference.interfaces.BaseNormalizer`. Its signature is
        fixed, so it cannot carry the line count; use
        :meth:`normalize_detailed` when the caller knows how many lines the
        plate had.

        Args:
            raw_text: The unmodified OCR output.

        Returns:
            A ``(normalized_text, is_valid_format)`` pair. An invalid result is
            still returned rather than discarded, so that recognition failures
            stay visible in the statistics.
        """
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
        decision = self.detect_plate_kind(cleaned, line_count=line_count)
        if decision.kind in CIVIL_KINDS:
            return NormalizationOutcome(
                raw_text=raw_text,
                cleaned_text=cleaned,
                text=cleaned,
                is_valid_format=True,
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
        repaired_decision = self.detect_plate_kind(repaired, line_count=line_count)
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

    def detect_plate_kind(self, text: str, line_count: int | None = None) -> KindDecision:
        """Classify a cleaned plate string.

        Patterns are tried in the priority order of
        :data:`~ai.inference.plate_rules.PATTERNS_BY_KIND`, and *all* matches
        are collected, because two ambiguities are documented and verified:

        ================= ============= ==============================
        Ambiguity         Example       Resolvable by
        ================= ============= ==============================
        car / old moto    ``29B11234``  line count, partially
        special / new mot ``29LD12345`` not by line count
        ================= ============= ==============================

        **What ``line_count`` can settle.** Motorcycles are always two-line
        plates, so ``line_count=1`` proves the string is a car plate and the
        ambiguity disappears. ``line_count=2`` proves nothing on its own: a
        short car plate is two-line too, so the pair stays ambiguous and the
        flag remains set. Claiming otherwise would fabricate information the
        input does not contain.

        Args:
            text: A cleaned string (digits and upper-case letters only).
            line_count: ``1`` or ``2`` when known, otherwise ``None``. Any
                other value is ignored.

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
        best = candidates[0]
        resolved = False

        if (
            is_ambiguous
            and line_count == 1
            and {PlateKind.CAR, PlateKind.MOTORCYCLE_OLD} <= candidate_set
        ):
            # A one-line plate cannot be a motorcycle plate (section 7.1).
            best = PlateKind.CAR
            is_ambiguous = any(
                pair <= candidate_set - {PlateKind.MOTORCYCLE_OLD} for pair in _AMBIGUOUS_PAIRS
            )
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

    def format_for_display(self, text: str, line_count: int | None = None) -> str:
        """Re-insert separators so a plate reads naturally in the UI.

        The canonical stored form is separator-free (section 7.5); separators
        are a presentation concern and are added back only here.

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
            line_count: ``1`` or ``2`` when known, forwarded to classification.

        Returns:
            The formatted string, or ``text`` unchanged when it matches no
            known pattern -- an unrecognised string is shown exactly as read,
            never dressed up to look valid.
        """
        decision = self.detect_plate_kind(text, line_count=line_count)
        if decision.kind is PlateKind.UNKNOWN:
            return text

        match = PATTERNS_BY_KIND[decision.kind].match(text)
        if match is None:  # pragma: no cover - guarded by detect_plate_kind
            return text
        groups = match.groupdict()

        if decision.kind is PlateKind.DIPLOMATIC:
            return (
                f"{groups['province']}-{groups['country']}-" f"{groups['code']}-{groups['number']}"
            )
        if decision.kind is PlateKind.MILITARY:
            return f"{groups['unit']}-{groups['number']}"

        number = groups["number"]
        prefix = text[: len(text) - len(number)]
        return f"{prefix}-{_group_number(number)}"


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
