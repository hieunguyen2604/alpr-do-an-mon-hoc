"""Post-processing: position-based repair and validation for Vietnamese plates (NFR-M1)."""

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
        """Run the full normalisation and report everything that happened."""
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
        """Classify a cleaned plate string."""
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
        """Return whether a cleaned string matches a known civil plate format."""
        return self.detect_plate_kind(text, line_count=line_count).kind in CIVIL_KINDS

    def format_for_display(
        self,
        text: str,
        line_count: int | None = None,
        kind: PlateKind | str | None = None,
        upper_char_count: int = 0,
    ) -> str:
        """Re-insert separators so a plate reads naturally in the UI."""
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
"""Families whose grouping is `serial-number` and therefore movable."""


def _group_number(number: str) -> str:
    """Insert the thousands dot into a plate's order-number group."""
    if len(number) == 5:
        return f"{number[:3]}.{number[3:]}"
    return number
