"""Tests for the Vietnamese plate rules and the normalizer."""

from __future__ import annotations

import re
import string

import pytest

from ai.inference.normalizer import VietnamesePlateNormalizer
from ai.inference.plate_rules import (
    CIVIL_KINDS,
    L11,
    L20,
    L20B,
    L21,
    OCR_SAFE_CHARSET,
    OCR_TRAINING_CHARSET,
    POSITION_MASKS,
    PROVINCE_CODES,
    RE_BLUE_CAR,
    RE_BLUE_MOTORCYCLE,
    RE_CAR,
    RE_DIPLOMATIC,
    RE_MILITARY,
    RE_MOTORCYCLE_ANY,
    RE_MOTORCYCLE_NEW,
    RE_MOTORCYCLE_OLD,
    RE_SPECIAL,
    TO_DIGIT,
    TO_LETTER,
    UNUSED_PROVINCE_CODES,
    PlateKind,
    apply_position_rules,
    clean_text,
)

ALL_PATTERNS: dict[str, re.Pattern[str]] = {
    "RE_CAR": RE_CAR,
    "RE_MOTORCYCLE_NEW": RE_MOTORCYCLE_NEW,
    "RE_MOTORCYCLE_OLD": RE_MOTORCYCLE_OLD,
    "RE_MOTORCYCLE_ANY": RE_MOTORCYCLE_ANY,
    "RE_BLUE_CAR": RE_BLUE_CAR,
    "RE_BLUE_MOTORCYCLE": RE_BLUE_MOTORCYCLE,
    "RE_SPECIAL": RE_SPECIAL,
    "RE_DIPLOMATIC": RE_DIPLOMATIC,
    "RE_MILITARY": RE_MILITARY,
}
"""The nine patterns of section 8.6, so "all 9 patterns" is literally testable."""


@pytest.fixture(scope="module")
def normalizer() -> VietnamesePlateNormalizer:
    """Return a shared normalizer; the class is stateless, so one is enough."""
    return VietnamesePlateNormalizer()


def _matching_patterns(text: str) -> set[str]:
    """Return the names of every pattern the string matches."""
    return {name for name, pattern in ALL_PATTERNS.items() if pattern.match(text)}


def _expand(char_class: str) -> str:
    """Expand a single-character regex class into the letters it accepts."""
    return "".join(c for c in string.ascii_uppercase if re.fullmatch(char_class, c))


# ---------------------------------------------------------------------------
# Section 8.2 / 8.6 -- constants
# ---------------------------------------------------------------------------


def test_province_code_counts() -> None:
    """81 codes are in use and exactly 8 two-digit codes are never issued."""
    assert len(PROVINCE_CODES) == 81
    assert UNUSED_PROVINCE_CODES == {"13", "42", "44", "45", "46", "87", "91", "96"}
    assert len(UNUSED_PROVINCE_CODES) == 8
    assert not PROVINCE_CODES & UNUSED_PROVINCE_CODES
    # Together they must tile the whole 11..99 range with no gap and no overlap.
    assert PROVINCE_CODES | UNUSED_PROVINCE_CODES == {str(code) for code in range(11, 100)}


@pytest.mark.parametrize(
    ("char_class", "expected"),
    [
        (L20, "ABCDEFGHKLMNPSTUVXYZ"),
        (L20B, "ABCDEFHKLMNPRSTUVXYZ"),
        (L11, "ABCDEFGHKLM"),
        (L21, "ABCDEFGHKLMNPRSTUVXYZ"),
    ],
    ids=["L20", "L20B", "L11", "L21"],
)
def test_character_classes_expand_as_documented(char_class: str, expected: str) -> None:
    """Each class expands to exactly the letters listed in section 8.6."""
    assert _expand(char_class) == expected


def test_serial_letter_sets_are_asymmetric() -> None:
    """The first serial letter allows ``G`` not ``R``; the second, the reverse."""
    first, second = _expand(L20), _expand(L20B)
    assert "G" in first and "R" not in first
    assert "R" in second and "G" not in second
    assert len(first) == len(second) == 20


def test_ocr_charsets() -> None:
    """31 characters are legal on a plate; a model is trained on all 36."""
    assert len(OCR_SAFE_CHARSET) == 31
    assert len(OCR_TRAINING_CHARSET) == 36
    assert set(OCR_SAFE_CHARSET) < set(OCR_TRAINING_CHARSET)
    # R must be reachable, otherwise every `29-AR ...` plate fails at the model
    # layer where no post-processing can repair it (section 5.2).
    assert "R" in OCR_SAFE_CHARSET
    for excluded in "IJOQW":
        assert excluded not in OCR_SAFE_CHARSET
        assert excluded in OCR_TRAINING_CHARSET


# ---------------------------------------------------------------------------
# Section 8.6 -- the regex verification table (17 cases)
# ---------------------------------------------------------------------------

SECTION_8_6_CASES: list[tuple[str, str, str, bool, set[str]]] = [
    (
        "30A-123.45",
        "30A12345",
        "RE_CAR",
        True,
        {"RE_CAR", "RE_MOTORCYCLE_OLD", "RE_MOTORCYCLE_ANY", "RE_BLUE_CAR", "RE_BLUE_MOTORCYCLE"},
    ),
    (
        "51K-999.99",
        "51K99999",
        "RE_CAR",
        True,
        {"RE_CAR", "RE_MOTORCYCLE_OLD", "RE_MOTORCYCLE_ANY", "RE_BLUE_CAR", "RE_BLUE_MOTORCYCLE"},
    ),
    (
        "29-AA 002.33",
        "29AA00233",
        "RE_MOTORCYCLE_NEW",
        True,
        {"RE_MOTORCYCLE_NEW", "RE_MOTORCYCLE_ANY"},
    ),
    (
        "29-HA 002.33",
        "29HA00233",
        "RE_MOTORCYCLE_NEW",
        True,
        {"RE_MOTORCYCLE_NEW", "RE_MOTORCYCLE_ANY"},
    ),
    (
        "29-B1 123.45",
        "29B112345",
        "RE_MOTORCYCLE_OLD",
        True,
        {"RE_MOTORCYCLE_OLD", "RE_MOTORCYCLE_ANY", "RE_BLUE_MOTORCYCLE"},
    ),
    (
        "80B-001.23",
        "80B00123",
        "RE_CAR",
        True,
        {"RE_CAR", "RE_BLUE_CAR"},
    ),
    (
        "80B1-234.56",
        "80B123456",
        "RE_MOTORCYCLE_OLD",
        True,
        {"RE_MOTORCYCLE_OLD", "RE_MOTORCYCLE_ANY", "RE_BLUE_MOTORCYCLE"},
    ),
    (
        "29LD-123.45",
        "29LD12345",
        "RE_SPECIAL",
        True,
        {"RE_SPECIAL", "RE_MOTORCYCLE_NEW", "RE_MOTORCYCLE_ANY"},
    ),
    (
        "80-001-NG-01",
        "80001NG01",
        "RE_DIPLOMATIC",
        True,
        {"RE_DIPLOMATIC"},
    ),
    (
        "TM-1234",
        "TM1234",
        "RE_MILITARY",
        True,
        {"RE_MILITARY"},
    ),
    ("13A-123.45", "13A12345", "RE_CAR", False, set()),
    ("30I-123.45", "30I12345", "RE_CAR", False, set()),
    ("30O-123.45", "30O12345", "RE_CAR", False, set()),
    ("29-AG 123.45", "29AG12345", "RE_MOTORCYCLE_NEW", False, set()),
    (
        "29-AR 123.45",
        "29AR12345",
        "RE_MOTORCYCLE_NEW",
        True,
        {"RE_MOTORCYCLE_NEW", "RE_MOTORCYCLE_ANY"},
    ),
    (
        "80N-123.45",
        "80N12345",
        "RE_BLUE_CAR",
        False,
        {"RE_CAR", "RE_MOTORCYCLE_OLD", "RE_MOTORCYCLE_ANY"},
    ),
    (
        "29B1-1234",
        "29B11234",
        "RE_CAR",
        True,
        {"RE_CAR", "RE_MOTORCYCLE_OLD", "RE_MOTORCYCLE_ANY", "RE_BLUE_CAR", "RE_BLUE_MOTORCYCLE"},
    ),
]
"""The section 8.6 table: raw input, cleaned form, pattern under test, expected"""


@pytest.mark.parametrize(
    ("raw", "cleaned", "pattern_name", "expected", "all_matches"),
    SECTION_8_6_CASES,
    ids=[case[0] for case in SECTION_8_6_CASES],
)
def test_section_8_6_regex_table(
    raw: str,
    cleaned: str,
    pattern_name: str,
    expected: bool,
    all_matches: set[str],
) -> None:
    """Reproduce every row of the section 8.6 verification table."""
    assert clean_text(raw) == cleaned
    assert bool(ALL_PATTERNS[pattern_name].match(cleaned)) is expected
    assert _matching_patterns(cleaned) == all_matches


def test_eight_character_string_is_ambiguous() -> None:
    """``29B11234`` matches the car and the old-motorcycle pattern at once."""
    assert RE_CAR.match("29B11234")
    assert RE_MOTORCYCLE_OLD.match("29B11234")


def test_special_code_collides_with_new_motorcycle_serial() -> None:
    """``29LD12345`` matches both a special code and a two-letter serial."""
    special = RE_SPECIAL.match("29LD12345")
    motorcycle = RE_MOTORCYCLE_NEW.match("29LD12345")
    assert special is not None and special.group("code") == "LD"
    assert motorcycle is not None
    # `RM` escapes the collision because R is not in the first-letter set.
    assert RE_SPECIAL.match("29RM12345")
    assert RE_MOTORCYCLE_NEW.match("29RM12345") is None


# ---------------------------------------------------------------------------
# Section 9.7 -- the position-mask repair table (6 cases)
# ---------------------------------------------------------------------------

SECTION_9_7_CASES: list[tuple[str, str, str]] = [
    ("3OA12345", "car_5", "30A12345"),
    ("30012345", "car_5", "30D12345"),
    ("29AA1234S", "motorcycle_9", "29AA12345"),
    ("Z9AA12345", "motorcycle_9", "29AA12345"),
    ("29B112345", "motorcycle_9", "29B112345"),
    ("3OB12E45", "car_5", "30B12E45"),
]
"""The section 9.7 table: raw string, mask key, expected repaired string."""


@pytest.mark.parametrize(
    ("raw", "mask_key", "expected"),
    SECTION_9_7_CASES,
    ids=[case[0] for case in SECTION_9_7_CASES],
)
def test_section_9_7_position_rules(raw: str, mask_key: str, expected: str) -> None:
    """Reproduce every row of the section 9.7 repair table."""
    assert apply_position_rules(raw, POSITION_MASKS[mask_key]) == expected


def test_unmapped_character_is_kept_verbatim() -> None:
    """An unknown character survives untouched -- no placeholder is inserted."""
    repaired = apply_position_rules("3OB12E45", POSITION_MASKS["car_5"])
    assert repaired == "30B12E45"
    assert "?" not in repaired
    assert not any(pattern.match(repaired) for pattern in ALL_PATTERNS.values())


def test_mask_length_mismatch_is_refused() -> None:
    """A mask of the wrong length leaves the string untouched."""
    assert apply_position_rules("30A1234", POSITION_MASKS["motorcycle_9"]) == "30A1234"


# ---------------------------------------------------------------------------
# Sections 8.5 / 9.4 -- the wildcard, the single forbidden repair position
# ---------------------------------------------------------------------------


def test_motorcycle_mask_has_wildcard_at_index_three() -> None:
    """The 9-character mask must not claim a type at the ambiguous position."""
    assert POSITION_MASKS["motorcycle_9"] == "DDL?DDDDD"
    assert POSITION_MASKS["motorcycle_9"][3] == "?"
    assert len(POSITION_MASKS) == 3


@pytest.mark.parametrize("plate", ["29AA12345", "29B112345"])
def test_wildcard_position_is_never_coerced(plate: str) -> None:
    """Both motorcycle styles pass through the shared mask unharmed."""
    repaired = apply_position_rules(plate, POSITION_MASKS["motorcycle_9"])
    assert repaired == plate
    assert repaired[3] == plate[3]


def test_wrong_masks_would_destroy_the_plates() -> None:
    """Show what the wildcard prevents, so the rule cannot be "simplified" away."""
    assert apply_position_rules("29AA12345", "DDLDDDDDD") == "29A412345"
    assert apply_position_rules("29B112345", "DDLLDDDDD") == "29BL12345"


# ---------------------------------------------------------------------------
# Section 9.3 -- the mapping is not symmetric
# ---------------------------------------------------------------------------


def test_confusion_mapping_is_asymmetric() -> None:
    """``O -> 0`` is valid; ``0 -> O`` never is -- ``0`` maps to ``D``."""
    assert TO_DIGIT["O"] == "0"
    assert TO_LETTER["0"] == "D"
    assert "O" not in TO_LETTER.values()
    # No excluded letter may ever be produced by a repair.
    for excluded in "IJOQW":
        assert excluded not in TO_LETTER.values()


def test_confusion_table_sizes() -> None:
    """The tables hold the 12 + 9 pairs listed in section 9.6."""
    assert len(TO_DIGIT) == 12
    assert len(TO_LETTER) == 9
    assert all(key.isalpha() and value.isdigit() for key, value in TO_DIGIT.items())
    assert all(key.isdigit() and value.isalpha() for key, value in TO_LETTER.items())


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("3OA12345", "30A12345"), ("30012345", "30D12345")],
)
def test_asymmetry_end_to_end(
    normalizer: VietnamesePlateNormalizer, raw: str, expected: str
) -> None:
    """``O`` at a digit slot becomes ``0``; ``0`` at a letter slot becomes ``D``."""
    text, is_valid = normalizer.normalize(raw)
    assert (text, is_valid) == (expected, True)


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("30A-123.45", "30A12345"),
        ("  29 - AA  123.45 ", "29AA12345"),
        ("29-mđ 002.33", "29MD00233"),
        ("51TĐ-12345", "51TD12345"),
        ("30A\n12345", "30A12345"),
        ("", ""),
        ("...---...", ""),
    ],
)
def test_clean_text(raw: str, expected: str) -> None:
    """Separators, whitespace, case and the ``Đ`` stroke are all folded away."""
    assert clean_text(raw) == expected


# ---------------------------------------------------------------------------
# Normalizer behaviour
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    ["30A-123.45", "29-AA 002.33", "29-B1 123.45", "29-AR 123.45", "80B-001.23"],
)
def test_valid_plates_pass_through_untouched(
    normalizer: VietnamesePlateNormalizer, raw: str
) -> None:
    """A string that is already valid must not be modified (operating rule 1)."""
    outcome = normalizer.normalize_detailed(raw)
    assert outcome.is_valid_format is True
    assert outcome.text == clean_text(raw)
    assert outcome.corrections == ()


@pytest.mark.parametrize(
    "raw",
    [
        "13A-123.45",  # province code 13 is never issued
        "30I-123.45",  # I is not a serial letter
        "30O-123.45",  # O is not a serial letter
        "29-AG 123.45",  # G is not valid as the second serial letter
        "3OB12E45",  # unrepairable character in a digit slot
        "ABC",  # far too short
        "",  # nothing at all
        "!!!",  # nothing survives cleaning
        "30A123456789",  # far too long
    ],
)
def test_invalid_plates_are_reported_not_discarded(
    normalizer: VietnamesePlateNormalizer, raw: str
) -> None:
    """Invalid input yields ``is_valid_format=False`` and is still returned."""
    text, is_valid = normalizer.normalize(raw)
    assert is_valid is False
    assert isinstance(text, str)
    # The raw string is always preserved for the audit trail (operating rule 2).
    assert normalizer.normalize_detailed(raw).raw_text == raw


def test_normalize_returns_the_interface_contract(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """``normalize`` returns exactly a ``(str, bool)`` pair."""
    result = normalizer.normalize("30A-123.45")
    assert isinstance(result, tuple) and len(result) == 2
    assert isinstance(result[0], str) and isinstance(result[1], bool)


def test_military_plate_is_recognised_but_not_valid(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """Army plates match their pattern yet are excluded from valid civil formats."""
    assert RE_MILITARY.match("TM1234")
    assert normalizer.detect_plate_kind("TM1234").kind is PlateKind.MILITARY
    assert normalizer.is_valid_format("TM1234") is False
    assert PlateKind.MILITARY not in CIVIL_KINDS


# ---------------------------------------------------------------------------
# Ambiguity handling
# ---------------------------------------------------------------------------


def test_eight_character_ambiguity_is_flagged(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """Without a line count, ``29B11234`` is reported as ambiguous."""
    decision = normalizer.detect_plate_kind("29B11234")
    assert decision.is_ambiguous is True
    assert PlateKind.CAR in decision.candidates
    assert PlateKind.MOTORCYCLE_OLD in decision.candidates
    assert decision.resolved_by_line_count is False


def test_one_line_count_resolves_the_eight_character_ambiguity(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """A one-line plate cannot be a motorcycle, so the ambiguity disappears."""
    decision = normalizer.detect_plate_kind("29B11234", line_count=1)
    assert decision.kind is PlateKind.CAR
    assert decision.is_ambiguous is False
    assert decision.resolved_by_line_count is True


def test_two_lines_prefers_the_motorcycle_but_stays_ambiguous(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """``line_count=2`` breaks the tie toward the motorcycle without claiming proof."""
    decision = normalizer.detect_plate_kind("29B11234", line_count=2)
    assert decision.kind is PlateKind.MOTORCYCLE_OLD
    assert decision.resolved_by_line_count is True
    assert decision.is_ambiguous is True, "two lines is a prior, not a proof"


def test_printed_dot_in_raw_text_proves_the_car_reading(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """A ``DDD.DD`` group in the raw string beats the two-line motorcycle prior."""
    decision = normalizer.detect_plate_kind(
        "51H60969", line_count=2, raw_text="51H 609.69"
    )
    assert decision.kind is PlateKind.CAR
    assert decision.is_ambiguous is False, "a printed dot is proof, not a prior"

    # Without the dot the measured motorcycle prior stands untouched.
    plain = normalizer.detect_plate_kind("51P54578", line_count=2, raw_text="51-P5 4578")
    assert plain.kind is PlateKind.MOTORCYCLE_OLD


def test_dot_evidence_flows_through_normalize_detailed(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """The end-to-end path: raw string in, car verdict and car grouping out."""
    outcome = normalizer.normalize_detailed("51C 920.87", line_count=2)
    assert outcome.text == "51C92087"
    assert outcome.decision.kind is PlateKind.CAR
    assert (
        normalizer.format_for_display(outcome.text, kind=outcome.decision.kind)
        == "51C-920.87"
    )


def test_the_upper_line_outranks_the_family_for_digit_grouping(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """Where the plate's own line break falls beats any inference from the string."""
    assert (
        normalizer.format_for_display(
            "67C10815", line_count=2, kind=PlateKind.CAR, upper_char_count=4
        )
        == "67C1-0815"
    )
    assert (
        normalizer.format_for_display(
            "77H54374", line_count=2, kind=PlateKind.CAR, upper_char_count=4
        )
        == "77H5-4374"
    )
    assert (
        normalizer.format_for_display(
            "51H60969", line_count=2, kind=PlateKind.MOTORCYCLE_OLD, upper_char_count=3
        )
        == "51H-609.69"
    )
    # No observation -> the family decides, exactly as before this parameter.
    assert (
        normalizer.format_for_display(
            "67C10815", line_count=2, kind=PlateKind.CAR, upper_char_count=0
        )
        == "67C-108.15"
    )
    # A count the plate rules cannot honour is ignored rather than applied: the
    # implied number would be six digits, which no Vietnamese layout carries.
    assert (
        normalizer.format_for_display(
            "67C10815", line_count=2, kind=PlateKind.CAR, upper_char_count=2
        )
        == "67C-108.15"
    )
    # One-line plates have no upper line; a stray count must not regroup them.
    assert (
        normalizer.format_for_display(
            "51H60969", line_count=1, kind=PlateKind.CAR, upper_char_count=4
        )
        == "51H-609.69"
    )


def test_format_for_display_follows_the_established_kind(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """The digit grouping must tell the same story as the family badge."""
    assert normalizer.format_for_display("51H60969", kind=PlateKind.CAR) == "51H-609.69"
    assert (
        normalizer.format_for_display("51H60969", kind=PlateKind.MOTORCYCLE_OLD)
        == "51H6-0969"
    )
    # String value works too -- the pipeline carries kinds as strings.
    assert normalizer.format_for_display("51H60969", kind="car") == "51H-609.69"
    # A kind the string cannot carry is ignored, not obeyed.
    assert (
        normalizer.format_for_display("51H60969", line_count=1, kind="diplomatic")
        == "51H-609.69"
    )


def test_two_line_preference_only_applies_to_the_car_motorcycle_tie(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """A two-line plate whose string is unambiguous must be left alone."""
    decision = normalizer.detect_plate_kind("65A00450", line_count=2)
    assert decision.kind is PlateKind.CAR


def test_special_code_ambiguity_prefers_the_closed_list(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """``29LD12345`` classifies as a special code but stays flagged as ambiguous."""
    decision = normalizer.detect_plate_kind("29LD12345")
    assert decision.kind is PlateKind.SPECIAL
    assert PlateKind.MOTORCYCLE_NEW in decision.candidates
    assert decision.is_ambiguous is True


def test_unambiguous_plate_is_not_flagged(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """A plain new-style motorcycle plate carries no ambiguity flag."""
    decision = normalizer.detect_plate_kind("29AA12345")
    assert decision.kind is PlateKind.MOTORCYCLE_NEW
    assert decision.is_ambiguous is False


# ---------------------------------------------------------------------------
# Display formatting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("30A12345", "30A-123.45"),
        ("51A12345", "51A-123.45"),
        ("29A1234", "29A-1234"),
        ("29AA12345", "29AA-123.45"),
        ("29B112345", "29B1-123.45"),
        ("80001NG01", "80-001-NG-01"),
        ("NOTAPLATE", "NOTAPLATE"),
    ],
)
def test_format_for_display(
    normalizer: VietnamesePlateNormalizer, text: str, expected: str
) -> None:
    """Separators come back only for presentation; unknown strings are untouched."""
    assert normalizer.format_for_display(text) == expected


def test_display_form_round_trips(normalizer: VietnamesePlateNormalizer) -> None:
    """Cleaning a displayed plate returns the canonical stored form."""
    for text in ("30A12345", "29AA12345", "29A1234"):
        assert clean_text(normalizer.format_for_display(text)) == text


# ---------------------------------------------------------------------------
# Corrections audit trail
# ---------------------------------------------------------------------------


def test_corrections_are_reported_with_positions(
    normalizer: VietnamesePlateNormalizer,
) -> None:
    """Every repaired character is reported as ``(index, before, after)``."""
    outcome = normalizer.normalize_detailed("Z9AA1234S")
    assert outcome.text == "29AA12345"
    assert outcome.is_valid_format is True
    assert outcome.corrections == ((0, "Z", "2"), (8, "S", "5"))
    assert outcome.was_corrected is True
