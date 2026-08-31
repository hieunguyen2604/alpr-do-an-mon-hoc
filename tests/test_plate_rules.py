"""Unit tests for :mod:`ai.inference.plate_rules`."""

from __future__ import annotations

import pytest

from ai.inference.normalizer import VietnamesePlateNormalizer
from ai.inference.plate_rules import (
    CIVIL_KINDS,
    EXCLUDED_LETTERS,
    MASK_BY_LENGTH,
    MASK_DIGIT,
    MASK_LETTER,
    MASK_WILDCARD,
    OCR_SAFE_CHARSET,
    OCR_TRAINING_CHARSET,
    PATTERNS_BY_KIND,
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
    SPECIAL_SERIAL_CODES,
    TO_DIGIT,
    TO_LETTER,
    UNUSED_PROVINCE_CODES,
    PlateKind,
    apply_position_rules,
    clean_text,
    mask_for_length,
)


class TestProvinceCodes:
    """The province table and the set of codes deliberately never issued."""

    def test_has_the_documented_number_of_codes(self) -> None:
        assert len(PROVINCE_CODES) == 81

    def test_used_and_unused_codes_do_not_overlap(self) -> None:
        assert PROVINCE_CODES & UNUSED_PROVINCE_CODES == frozenset()

    def test_the_two_sets_together_cover_11_to_99(self) -> None:
        """Every two-digit code from 11 to 99 is accounted for as used or not."""
        covered = PROVINCE_CODES | UNUSED_PROVINCE_CODES
        expected = {str(value) for value in range(11, 100)}
        assert covered == expected

    @pytest.mark.parametrize("code", ["13", "42", "44", "45", "46", "87", "91", "96"])
    def test_an_unissued_code_is_rejected_by_the_car_pattern(self, code: str) -> None:
        """``13A-123.45`` must fail: the code 13 has never been issued."""
        assert RE_CAR.match(f"{code}A12345") is None

    def test_a_valid_code_is_accepted(self) -> None:
        assert RE_CAR.match("51F12345") is not None


class TestCarPattern:
    """``<province><1 serial letter><4-5 digits>``."""

    @pytest.mark.parametrize(
        "text",
        ["51F12345", "30A12345", "29B1234", "80N12345", "99Z99999"],
    )
    def test_accepts_a_well_formed_car_plate(self, text: str) -> None:
        assert RE_CAR.match(text) is not None

    @pytest.mark.parametrize(
        "text",
        [
            "51F123",  # too few digits
            "51F123456",  # too many digits
            "51I12345",  # I is excluded system-wide
            "51O12345",  # O is excluded system-wide
            "51Q12345",  # Q is excluded system-wide
            "51W12345",  # W is excluded system-wide
            "51R12345",  # R is not a first-position serial letter
            "5F12345",  # province code truncated
            "51-F-12345",  # separators must be cleaned first
        ],
    )
    def test_rejects_a_malformed_car_plate(self, text: str) -> None:
        assert RE_CAR.match(text) is None

    def test_captures_the_three_groups(self) -> None:
        match = RE_CAR.match("51F12345")
        assert match is not None
        assert match.group("province") == "51"
        assert match.group("serial") == "F"
        assert match.group("number") == "12345"

    def test_four_digit_plates_still_match(self) -> None:
        """Older 4-digit plates remain legally valid and must never be dropped."""
        match = RE_CAR.match("29B1234")
        assert match is not None
        assert match.group("number") == "1234"


class TestMotorcycleSerialAsymmetry:
    """L20 versus L20B -- the difference between ``G`` and ``R``."""

    def test_r_is_valid_in_the_second_serial_position(self) -> None:
        assert RE_MOTORCYCLE_NEW.match("29AR12345") is not None

    def test_g_is_not_valid_in_the_second_serial_position(self) -> None:
        assert RE_MOTORCYCLE_NEW.match("29AG12345") is None

    def test_g_is_valid_in_the_first_serial_position(self) -> None:
        assert RE_MOTORCYCLE_NEW.match("29GA12345") is not None

    def test_r_is_not_valid_in_the_first_serial_position(self) -> None:
        assert RE_MOTORCYCLE_NEW.match("29RA12345") is None

    def test_the_two_sets_really_are_mirror_images(self) -> None:
        """A single test stating the whole relationship between L20 and L20B."""
        first_ok = {
            letter
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if RE_MOTORCYCLE_NEW.match(f"29{letter}A12345") is not None
        }
        second_ok = {
            letter
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if RE_MOTORCYCLE_NEW.match(f"29A{letter}12345") is not None
        }
        assert len(first_ok) == 20
        assert len(second_ok) == 20
        assert first_ok - second_ok == {"G"}
        assert second_ok - first_ok == {"R"}


class TestMotorcyclePatterns:
    """New (two-letter) and old (letter + digit) motorcycle serials."""

    def test_new_style_matches(self) -> None:
        match = RE_MOTORCYCLE_NEW.match("29AA12345")
        assert match is not None
        assert match.group("serial1") == "A"
        assert match.group("serial2") == "A"

    def test_old_style_matches(self) -> None:
        match = RE_MOTORCYCLE_OLD.match("29B112345")
        assert match is not None
        assert match.group("serial2") == "1"

    def test_the_old_style_serial_digit_is_never_zero(self) -> None:
        """A ``0`` at this position is certainly an OCR error, not a plate."""
        assert RE_MOTORCYCLE_OLD.match("29B012345") is None

    @pytest.mark.parametrize("text", ["29AA12345", "29B112345"])
    def test_the_any_pattern_accepts_both_styles(self, text: str) -> None:
        assert RE_MOTORCYCLE_ANY.match(text) is not None

    def test_the_any_pattern_still_rejects_a_zero_serial(self) -> None:
        assert RE_MOTORCYCLE_ANY.match("29A012345") is None


class TestBluePlates:
    """State-agency plates, whose serial is restricted to 11 letters."""

    @pytest.mark.parametrize("letter", list("ABCDEFGHKLM"))
    def test_accepts_the_eleven_blue_letters(self, letter: str) -> None:
        assert RE_BLUE_CAR.match(f"80{letter}12345") is not None

    @pytest.mark.parametrize("letter", ["N", "P", "S", "T", "U", "V", "X", "Y", "Z"])
    def test_rejects_a_letter_outside_the_blue_set(self, letter: str) -> None:
        assert RE_BLUE_CAR.match(f"80{letter}12345") is None

    def test_a_blue_rejection_does_not_mean_the_plate_is_invalid(self) -> None:
        """``80N12345`` fails the blue pattern but is a perfectly valid car plate."""
        assert RE_BLUE_CAR.match("80N12345") is None
        assert RE_CAR.match("80N12345") is not None

    def test_blue_motorcycle_requires_a_digit_one_to_nine(self) -> None:
        assert RE_BLUE_MOTORCYCLE.match("80A112345") is not None
        assert RE_BLUE_MOTORCYCLE.match("80A012345") is None


class TestSpecialAndDiplomatic:
    """Special serial codes and diplomatic plates."""

    @pytest.mark.parametrize("code", SPECIAL_SERIAL_CODES)
    def test_every_declared_special_code_matches(self, code: str) -> None:
        assert RE_SPECIAL.match(f"51{code}12345") is not None

    def test_two_character_codes_are_preferred_over_one(self) -> None:
        """``RM`` must be captured whole, not as ``R`` followed by ``M12345``."""
        match = RE_SPECIAL.match("51RM12345")
        assert match is not None
        assert match.group("code") == "RM"

    def test_the_d_stroke_codes_are_stored_in_ascii_form(self) -> None:
        """A Latin-charset recogniser returns ``D`` for ``Đ``; MD/TD reflect that."""
        assert "MD" in SPECIAL_SERIAL_CODES
        assert "TD" in SPECIAL_SERIAL_CODES

    @pytest.mark.parametrize("code", ["NG", "QT", "CV", "NN"])
    def test_diplomatic_plates_match(self, code: str) -> None:
        match = RE_DIPLOMATIC.match(f"80123{code}45")
        assert match is not None
        assert match.group("country") == "123"
        assert match.group("code") == code

    def test_diplomatic_number_accepts_two_or_three_digits(self) -> None:
        assert RE_DIPLOMATIC.match("80123NG45") is not None
        assert RE_DIPLOMATIC.match("80123NG456") is not None
        assert RE_DIPLOMATIC.match("80123NG4") is None


class TestMilitaryIsRecognisedToBeExcluded:
    """Army plates match a pattern but are never a valid civil format."""

    def test_the_pattern_matches_an_army_plate(self) -> None:
        assert RE_MILITARY.match("KA1234") is not None

    def test_military_is_not_a_civil_kind(self) -> None:
        assert PlateKind.MILITARY not in CIVIL_KINDS

    def test_every_other_declared_kind_except_unknown_is_civil(self) -> None:
        non_civil = set(PATTERNS_BY_KIND) - CIVIL_KINDS
        assert non_civil == {PlateKind.MILITARY}


class TestPatternPriority:
    """The classification order encoded in ``PATTERNS_BY_KIND``."""

    def test_diplomatic_comes_first_and_military_last(self) -> None:
        order = list(PATTERNS_BY_KIND)
        assert order[0] is PlateKind.DIPLOMATIC
        assert order[-1] is PlateKind.MILITARY

    def test_special_is_tried_before_the_motorcycle_patterns(self) -> None:
        """``29LD12345`` matches both; the special code must win."""
        order = list(PATTERNS_BY_KIND)
        assert order.index(PlateKind.SPECIAL) < order.index(PlateKind.MOTORCYCLE_NEW)
        assert RE_SPECIAL.match("29LD12345") is not None
        assert RE_MOTORCYCLE_NEW.match("29LD12345") is not None

    def test_car_precedes_old_motorcycle_as_a_tie_break(self) -> None:
        order = list(PATTERNS_BY_KIND)
        assert order.index(PlateKind.CAR) < order.index(PlateKind.MOTORCYCLE_OLD)


class TestCharsets:
    """The recognition and training charsets, and the excluded letters."""

    def test_five_letters_are_excluded_system_wide(self) -> None:
        assert EXCLUDED_LETTERS == frozenset({"I", "J", "O", "Q", "W"})

    def test_r_is_not_excluded(self) -> None:
        """The earlier "6 excluded letters" figure was corrected; R stays valid."""
        assert "R" not in EXCLUDED_LETTERS

    def test_the_safe_charset_has_31_characters(self) -> None:
        assert len(OCR_SAFE_CHARSET) == 31
        assert len(set(OCR_SAFE_CHARSET)) == 31

    def test_the_safe_charset_contains_no_excluded_letter(self) -> None:
        assert EXCLUDED_LETTERS.isdisjoint(set(OCR_SAFE_CHARSET))

    def test_the_safe_charset_contains_r(self) -> None:
        """A charset without ``R`` fails systematically on every ``29AR`` plate."""
        assert "R" in OCR_SAFE_CHARSET

    def test_the_training_charset_is_the_full_alphabet(self) -> None:
        """Train on 36, constrain to 31: an illegal prediction stays observable."""
        assert len(OCR_TRAINING_CHARSET) == 36
        assert set(OCR_SAFE_CHARSET).issubset(set(OCR_TRAINING_CHARSET))


class TestCleanText:
    """Reduction of raw OCR output to canonical alphanumeric form."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("30A-123.45", "30A12345"),
            ("51F 123 45", "51F12345"),
            ("  29-AA 123.45  ", "29AA12345"),
            ("29\nAA\n12345", "29AA12345"),
            ("51f12345", "51F12345"),
            ("29-mđ 002.33", "29MD00233"),
            ("29MĐ00233", "29MD00233"),
            ("", ""),
            ("---...", ""),
            ("51F*12345#", "51F12345"),
        ],
    )
    def test_cleans_as_documented(self, raw: str, expected: str) -> None:
        assert clean_text(raw) == expected

    def test_output_contains_only_digits_and_upper_case_letters(self) -> None:
        cleaned = clean_text("  a1!b2@c3#  đ  ")
        assert cleaned.isalnum()
        assert cleaned == cleaned.upper()


class TestMaskSelection:
    """Which mask applies to a cleaned string of a given length."""

    @pytest.mark.parametrize(
        ("length", "mask"),
        [(7, "DDLDDDD"), (8, "DDLDDDDD"), (9, "DDL?DDDDD")],
    )
    def test_returns_the_documented_mask(self, length: int, mask: str) -> None:
        assert mask_for_length(length) == mask

    @pytest.mark.parametrize("length", [0, 1, 6, 10, 15])
    def test_returns_none_outside_the_plausible_range(self, length: int) -> None:
        """Too damaged for position-based repair: fail in a controlled way."""
        assert mask_for_length(length) is None

    def test_every_mask_length_matches_its_key(self) -> None:
        for length, mask in MASK_BY_LENGTH.items():
            assert len(mask) == length

    def test_masks_use_only_the_three_declared_symbols(self) -> None:
        allowed = {MASK_DIGIT, MASK_LETTER, MASK_WILDCARD}
        for mask in POSITION_MASKS.values():
            assert set(mask) <= allowed


class TestWildcardAtIndexThree:
    """The forbidden zone: index 3 of the 9-character motorcycle mask."""

    def test_index_three_is_a_wildcard(self) -> None:
        assert POSITION_MASKS["motorcycle_9"][3] == MASK_WILDCARD

    def test_it_is_the_only_wildcard_in_any_mask(self) -> None:
        wildcards = [
            (name, index)
            for name, mask in POSITION_MASKS.items()
            for index, symbol in enumerate(mask)
            if symbol == MASK_WILDCARD
        ]
        assert wildcards == [("motorcycle_9", 3)]

    def test_new_style_survives_the_mask_untouched(self) -> None:
        assert apply_position_rules("29AA12345", POSITION_MASKS["motorcycle_9"]) == "29AA12345"

    def test_old_style_survives_the_mask_untouched(self) -> None:
        assert apply_position_rules("29B112345", POSITION_MASKS["motorcycle_9"]) == "29B112345"

    def test_a_letter_at_the_wildcard_is_not_pushed_to_a_digit(self) -> None:
        """``A`` sits in TO_DIGIT; the wildcard must stop it being consulted."""
        assert "A" in TO_DIGIT
        assert apply_position_rules("29AA12345", "DDL?DDDDD")[3] == "A"

    def test_a_digit_at_the_wildcard_is_not_pushed_to_a_letter(self) -> None:
        """``1`` sits in TO_LETTER; the wildcard must stop it being consulted."""
        assert "1" in TO_LETTER
        assert apply_position_rules("29B112345", "DDL?DDDDD")[3] == "1"

    def test_the_wrong_masks_would_break_each_style(self) -> None:
        """Reproduces the two failures documented on ``POSITION_MASKS``."""
        assert apply_position_rules("29AA12345", "DDLDDDDDD") == "29A412345"
        assert apply_position_rules("29B112345", "DDLLDDDDD") == "29BL12345"


class TestApplyPositionRules:
    """Repair of OCR confusions against a position mask."""

    @pytest.mark.parametrize(
        ("text", "mask", "expected"),
        [
            ("3OA12345", POSITION_MASKS["car_5"], "30A12345"),
            ("30012345", POSITION_MASKS["car_5"], "30D12345"),
            ("30A1234S", POSITION_MASKS["car_5"], "30A12345"),
            ("3OA1234", POSITION_MASKS["car_4"], "30A1234"),
        ],
    )
    def test_repairs_as_documented(self, text: str, mask: str, expected: str) -> None:
        assert apply_position_rules(text, mask) == expected

    def test_a_correct_string_is_left_alone(self) -> None:
        assert apply_position_rules("51F12345", POSITION_MASKS["car_5"]) == "51F12345"

    def test_an_unmappable_character_is_kept_not_replaced(self) -> None:
        """``3OB12E45`` becomes ``30B12E45``, never ``30B12?45``."""
        result = apply_position_rules("3OB12E45", POSITION_MASKS["car_5"])
        assert result == "30B12E45"
        assert MASK_WILDCARD not in result

    def test_a_mismatched_mask_length_returns_the_input_unchanged(self) -> None:
        """Realigning would corrupt every position after the first discrepancy."""
        assert apply_position_rules("29AA12345", POSITION_MASKS["car_5"]) == "29AA12345"
        assert apply_position_rules("", POSITION_MASKS["car_5"]) == ""

    def test_the_mask_symbol_never_appears_in_output(self) -> None:
        for text in ("29AA12345", "3OB12E45", "30012345"):
            mask = mask_for_length(len(text))
            assert mask is not None
            assert MASK_WILDCARD not in apply_position_rules(text, mask)


class TestConfusionTableAsymmetry:
    """``O -> 0`` is right; ``0 -> O`` is never right."""

    def test_o_maps_to_zero_at_a_digit_position(self) -> None:
        assert TO_DIGIT["O"] == "0"

    def test_zero_maps_to_d_not_to_o_at_a_letter_position(self) -> None:
        assert TO_LETTER["0"] == "D"

    def test_no_excluded_letter_is_ever_produced(self) -> None:
        """The letter table must never emit ``I``, ``J``, ``O``, ``Q`` or ``W``."""
        assert EXCLUDED_LETTERS.isdisjoint(set(TO_LETTER.values()))

    def test_the_tables_are_not_mutual_inverses(self) -> None:
        round_tripped = {
            letter: TO_LETTER.get(digit) for letter, digit in TO_DIGIT.items() if digit in TO_LETTER
        }
        differing = {letter for letter, back in round_tripped.items() if back != letter}
        assert differing, "the tables would be symmetric, which the module denies"
        assert "O" in differing

    def test_to_digit_maps_letters_to_digits(self) -> None:
        for source, target in TO_DIGIT.items():
            assert source.isalpha()
            assert target.isdigit()

    def test_to_letter_maps_digits_to_letters(self) -> None:
        for source, target in TO_LETTER.items():
            assert source.isdigit()
            assert target.isalpha()

    def test_every_produced_letter_is_in_the_safe_charset(self) -> None:
        assert set(TO_LETTER.values()) <= set(OCR_SAFE_CHARSET)


class TestEndToEndRepair:
    """clean -> select mask -> repair, the sequence the normalizer performs."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("3OA-123.45", "30A12345"),
            ("51F-1234S", "51F12345"),
            ("29-AA 123.45", "29AA12345"),
            ("29-B1 123.45", "29B112345"),
        ],
    )
    def test_a_damaged_reading_is_repaired_into_a_valid_plate(
        self, raw: str, expected: str
    ) -> None:
        cleaned = clean_text(raw)
        mask = mask_for_length(len(cleaned))
        assert mask is not None
        repaired = apply_position_rules(cleaned, mask)
        assert repaired == expected
        assert any(
            pattern.match(repaired) is not None
            for kind, pattern in PATTERNS_BY_KIND.items()
            if kind in CIVIL_KINDS
        )


class TestMilitaryLayouts:
    """All six layouts of Annex II to the 2021 Ministry of National Defence rules."""

    @pytest.mark.parametrize(
        ("plate", "layout"),
        [
            ("AB1234", "ô tô, xe xích — biển dài"),
            ("AB123456", "ô tô, số hiệu 6 chữ số"),
            ("AB123", "mô tô"),
            ("AB123RM", "rơ moóc"),
            ("AB123BM", "sơ mi rơ moóc"),
            ("ABS1234", "xe máy chuyên dùng, hậu tố S"),
            ("ABL1234", "xe máy chuyên dùng, hậu tố L"),
            ("ABX1234", "xe máy chuyên dùng, hậu tố X"),
            ("KV6938", "mã đơn vị có thật"),
        ],
    )
    def test_every_layout_is_recognised_as_military(self, plate: str, layout: str) -> None:
        assert RE_MILITARY.match(plate) is not None, layout

    @pytest.mark.parametrize("plate", ["51F73420", "29AA12345", "80001NG01", "51LD12345"])
    def test_civil_plates_are_not_claimed_as_military(self, plate: str) -> None:
        """Widening the pattern must not let it swallow civil layouts."""
        assert RE_MILITARY.match(plate) is None


class TestMilitaryIsNeverReportedAsCivil:
    """An army plate must never reach a user labelled as a valid civilian plate."""

    @pytest.mark.parametrize(
        "plate",
        ["AB1234", "AB123", "AB123RM", "AB123BM", "ABS1234", "ABL1234", "ABX1234", "KV6938"],
    )
    def test_military_string_is_left_alone_and_flagged_invalid(self, plate: str) -> None:
        normalizer = VietnamesePlateNormalizer()
        outcome = normalizer.normalize_detailed(plate, line_count=1)

        assert outcome.decision.kind is PlateKind.MILITARY
        assert outcome.is_valid_format is False, "an army plate is not a civil format"
        assert outcome.text == plate, "repair must not rewrite a recognised army plate"

    def test_the_specific_string_that_used_to_become_a_fake_car_plate(self) -> None:
        normalizer = VietnamesePlateNormalizer()
        outcome = normalizer.normalize_detailed("ABS1234", line_count=1)

        assert outcome.text != "48S1234", "A→4 and B→8 must not be applied here"
        assert outcome.decision.kind is not PlateKind.CAR
