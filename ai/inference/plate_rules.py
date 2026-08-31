"""Vietnamese plate rules, regex patterns and character classes (TT 79/2024, QCVN 08:2024)."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Final

__all__ = [
    "PlateKind",
    "PROVINCE_CODES",
    "UNUSED_PROVINCE_CODES",
    "L20",
    "L20B",
    "L11",
    "L21",
    "EXCLUDED_LETTERS",
    "OCR_SAFE_CHARSET",
    "OCR_TRAINING_CHARSET",
    "SPECIAL_SERIAL_CODES",
    "RE_CAR",
    "RE_MOTORCYCLE_NEW",
    "RE_MOTORCYCLE_OLD",
    "RE_MOTORCYCLE_ANY",
    "RE_BLUE_CAR",
    "RE_BLUE_MOTORCYCLE",
    "RE_SPECIAL",
    "RE_DIPLOMATIC",
    "RE_MILITARY",
    "MILITARY_SPECIALISED_SUFFIXES",
    "MILITARY_TRAILER_SUFFIXES",
    "PATTERNS_BY_KIND",
    "CIVIL_KINDS",
    "POSITION_MASKS",
    "MASK_BY_LENGTH",
    "TO_DIGIT",
    "TO_LETTER",
    "MASK_DIGIT",
    "MASK_LETTER",
    "MASK_WILDCARD",
    "clean_text",
    "mask_for_length",
    "apply_position_rules",
]


# --- Plate kinds ---


class PlateKind(StrEnum):
    """The plate families this module can recognise."""

    CAR = "car"
    MOTORCYCLE_NEW = "motorcycle_new"
    MOTORCYCLE_OLD = "motorcycle_old"
    BLUE_CAR = "blue_car"
    BLUE_MOTORCYCLE = "blue_motorcycle"
    SPECIAL = "special"
    DIPLOMATIC = "diplomatic"
    MILITARY = "military"
    UNKNOWN = "unknown"


# --- Province codes (spec sections 4, 8.2) ---

PROVINCE_CODES: Final[frozenset[str]] = frozenset(
    {
        "11",
        "12",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "43",
        "47",
        "48",
        "49",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "72",
        "73",
        "74",
        "75",
        "76",
        "77",
        "78",
        "79",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
        "88",
        "89",
        "90",
        "92",
        "93",
        "94",
        "95",
        "97",
        "98",
        "99",
    }
)
"""The 81 province codes currently in use (Appendix of 51/2025/TT-BCA)."""

UNUSED_PROVINCE_CODES: Final[frozenset[str]] = frozenset(
    {"13", "42", "44", "45", "46", "87", "91", "96"}
)
"""The 8 two-digit codes that are deliberately never issued."""

_PROVINCE: Final[str] = "(?:" + "|".join(sorted(PROVINCE_CODES)) + ")"


# --- Serial character classes (sections 5.3, 8.2) ---

L20: Final[str] = r"[A-HK-NPS-VXYZ]"
"""The 20 standard serial letters: ``A B C D E F G H K L M N P S T U V X Y Z``."""

L20B: Final[str] = r"[A-FHK-NPRS-VXYZ]"
"""The 20 letters valid as the **second** serial letter of a motorcycle plate."""

L11: Final[str] = r"[A-HK-M]"
"""The 11 serial letters of blue state-agency plates: ``A``-``H``, ``K``, ``L``, ``M``."""

L21: Final[str] = r"[A-HK-NPR-VXYZ]"
"""The safe recognition charset: the 20 standard letters plus ``R``."""

# Aliases matching the constant names used in the specification document.
_L20: Final[str] = L20
_L20B: Final[str] = L20B
_L11: Final[str] = L11

EXCLUDED_LETTERS: Final[frozenset[str]] = frozenset({"I", "J", "O", "Q", "W"})
"""The 5 letters excluded from the plate system system-wide."""

_DIGITS: Final[str] = "0123456789"
_L21_LETTERS: Final[str] = "".join(
    letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if letter not in EXCLUDED_LETTERS
)

OCR_SAFE_CHARSET: Final[str] = _DIGITS + _L21_LETTERS
"""31 characters: 10 digits + the 21 letters that can legally appear on a plate."""

OCR_TRAINING_CHARSET: Final[str] = _DIGITS + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"""36 characters: the full ``0-9A-Z`` alphabet used to **train** a recogniser."""

SPECIAL_SERIAL_CODES: Final[tuple[str, ...]] = (
    "LD",
    "DA",
    "RM",
    "MK",
    "HC",
    "KT",
    "MD",
    "CD",
    "TD",
    "LB",
    "CT",
    "R",
    "T",
)
"""Special serial codes (section 5.4), in the order the pattern alternates them."""


# --- Patterns (section 8.3) ---

_NUM: Final[str] = r"\d{4,5}"
"""The order-number group: 5 digits today, 4 on older plates still in use."""

RE_CAR: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})" rf"(?P<serial>{L20})" rf"(?P<number>{_NUM})$"
)
"""White/yellow car plate: province + 1 serial letter + 4-5 digits."""

RE_MOTORCYCLE_NEW: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<serial1>{L20})"
    rf"(?P<serial2>{L20B})"
    rf"(?P<number>{_NUM})$"
)
"""Motorcycle plate issued from 15/08/2023: two-letter serial, e.g. ``29AA12345``."""

RE_MOTORCYCLE_OLD: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<serial1>{L20})"
    rf"(?P<serial2>[1-9])"
    rf"(?P<number>{_NUM})$"
)
"""Motorcycle plate issued before 15/08/2023: letter + digit serial, e.g. ``29B112345``."""

RE_MOTORCYCLE_ANY: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<serial1>{L20})"
    rf"(?P<serial2>[A-FHK-NPRS-VXYZ1-9])"
    rf"(?P<number>{_NUM})$"
)
"""Either motorcycle style, for a plain "is this a motorcycle plate" check."""

RE_BLUE_CAR: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})(?P<serial>{L11})(?P<number>{_NUM})$"
)
"""State-agency car plate: serial restricted to the 11 blue-plate letters."""

RE_BLUE_MOTORCYCLE: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})(?P<serial>{L11})" rf"(?P<digit>[1-9])(?P<number>{_NUM})$"
)
"""State-agency motorcycle plate: 11-letter serial + digit ``1``-``9``."""

RE_SPECIAL: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<code>{'|'.join(SPECIAL_SERIAL_CODES)})"
    rf"(?P<number>{_NUM})$"
)
"""Special serial codes: ``LD``, ``DA``, ``RM``, ``MK``, ``HC``, ``KT``, ``MD``, ..."""

RE_DIPLOMATIC: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<country>\d{{3}})"
    rf"(?P<code>NG|QT|CV|NN)"
    rf"(?P<number>\d{{2,3}})$"
)
"""Diplomatic/foreign plate: province + 3-digit country code + code + number."""

MILITARY_SPECIALISED_SUFFIXES: Final[tuple[str, ...]] = ("S", "L", "X")
"""Third letter marking an army *specialised machine* plate: ``ABS``, ``ABL``, ``ABX``."""

MILITARY_TRAILER_SUFFIXES: Final[tuple[str, ...]] = ("RM", "BM")
"""Trailer and semi-trailer codes, which follow the digits: ``AB123RM``, ``AB123BM``."""

RE_MILITARY: Final[re.Pattern[str]] = re.compile(
    r"^(?P<unit>[A-Z]{2})"
    rf"(?P<specialised>[{''.join(MILITARY_SPECIALISED_SUFFIXES)}]?)"
    r"(?P<number>\d{3,6})"
    rf"(?P<trailer>{'|'.join(MILITARY_TRAILER_SUFFIXES)})?$"
)
"""Army plate, which starts with a two-letter unit code instead of a province code."""

PATTERNS_BY_KIND: Final[dict[PlateKind, re.Pattern[str]]] = {
    PlateKind.DIPLOMATIC: RE_DIPLOMATIC,
    PlateKind.SPECIAL: RE_SPECIAL,
    PlateKind.MOTORCYCLE_NEW: RE_MOTORCYCLE_NEW,
    PlateKind.CAR: RE_CAR,
    PlateKind.MOTORCYCLE_OLD: RE_MOTORCYCLE_OLD,
    PlateKind.BLUE_CAR: RE_BLUE_CAR,
    PlateKind.BLUE_MOTORCYCLE: RE_BLUE_MOTORCYCLE,
    PlateKind.MILITARY: RE_MILITARY,
}
"""Patterns in classification priority order (see section 8.6, resolution 1)."""

CIVIL_KINDS: Final[frozenset[PlateKind]] = frozenset(
    {
        PlateKind.CAR,
        PlateKind.MOTORCYCLE_NEW,
        PlateKind.MOTORCYCLE_OLD,
        PlateKind.BLUE_CAR,
        PlateKind.BLUE_MOTORCYCLE,
        PlateKind.SPECIAL,
        PlateKind.DIPLOMATIC,
    }
)
"""Kinds that count as a valid civil plate format."""


# --- Position masks (sections 8.5, 9) ---

MASK_DIGIT: Final[str] = "D"
"""Mask symbol: this position must be a digit."""

MASK_LETTER: Final[str] = "L"
"""Mask symbol: this position must be a letter."""

MASK_WILDCARD: Final[str] = "?"
"""Mask symbol: both a letter and a digit are legal -- never coerce here."""

POSITION_MASKS: Final[dict[str, str]] = {
    "car_5": "DDLDDDDD",
    "car_4": "DDLDDDD",
    "motorcycle_9": "DDL?DDDDD",
}
"""Per-position type constraints, the foundation of every OCR repair rule."""

MASK_BY_LENGTH: Final[dict[int, str]] = {
    7: POSITION_MASKS["car_4"],
    8: POSITION_MASKS["car_5"],
    9: POSITION_MASKS["motorcycle_9"],
}
"""Mask selected purely by cleaned-string length (section 9.5)."""


# --- OCR confusion tables (section 9.6) ---

TO_DIGIT: Final[dict[str, str]] = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "J": "1",
    "L": "4",
    "Z": "2",
    "A": "4",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}
"""Table A: letter -> digit, applied only at positions the mask marks ``D``."""

TO_LETTER: Final[dict[str, str]] = {
    "0": "D",
    "1": "L",
    "2": "Z",
    "3": "B",
    "4": "A",
    "5": "S",
    "6": "G",
    "7": "Z",
    "8": "B",
}
"""Table B: digit -> letter, applied only at positions the mask marks ``L``."""

_SEPARATOR_RE: Final[re.Pattern[str]] = re.compile(r"[^0-9A-Z]")
_D_STROKE_TRANSLATION: Final[dict[int, str]] = str.maketrans({"Đ": "D", "đ": "D"})


# --- Pure functions ---


def clean_text(raw: str) -> str:
    """Reduce a raw OCR string to canonical alphanumeric form."""
    return _SEPARATOR_RE.sub("", raw.translate(_D_STROKE_TRANSLATION).upper())


def mask_for_length(length: int) -> str | None:
    """Return the position mask that applies to a cleaned string of this length."""
    return MASK_BY_LENGTH.get(length)


def apply_position_rules(text: str, mask: str) -> str:
    """Repair OCR confusions using the per-position type constraints."""
    if len(text) != len(mask):
        return text

    out: list[str] = []
    for char, kind in zip(text, mask, strict=True):
        if kind == MASK_WILDCARD:
            # Forbidden zone (section 9.4): letter AND digit both legal here, so the
            # character passes through untouched — a deliberate rule, not fall-through.
            out.append(char)
        elif kind == MASK_DIGIT and char.isalpha():
            out.append(TO_DIGIT.get(char, char))
        elif kind == MASK_LETTER and char.isdigit():
            out.append(TO_LETTER.get(char, char))
        else:
            out.append(char)
    return "".join(out)
