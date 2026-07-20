"""Vietnamese license plate standards expressed as data and pure functions.

This module is a **direct port** of the specification in
``docs/reports/01-vn-plate-standards.md`` (sections 8 and 9). Every constant
here was verified by running the reference script documented in section 8.6
(17 regex cases) and section 9.7 (6 position-mask cases). Nothing in this module
is re-derived or re-invented: when the law changes, the document is updated
first and this module follows it.

Legal basis
    Circular 79/2024/TT-BCA (in force 01/01/2025), amended by 13/2025/TT-BCA
    and 51/2025/TT-BCA (in force 01/07/2025); QCVN 08:2024/BCA for the physical
    plate dimensions.

Design rules this module obeys
    1. **Pure.** No I/O, no logging, no framework import, no mutable global
       state. Everything is a frozen constant or a function of its arguments,
       which makes the whole module trivially testable and safe to import from
       anywhere in the AI tier (NFR-M1).
    2. **Regexes are generated from sets, never hand-written.** The province
       group is built from :data:`PROVINCE_CODES`, so the patterns can never
       drift away from the table they are supposed to encode.
    3. **Character classes are named constants.** Two of them (:data:`L20` and
       :data:`L20B`) are still *well-founded hypotheses* rather than settled
       facts -- see the warning on :data:`L20B`. Isolating them means a future
       correction touches one line, not nine patterns.

Naming note
    The specification document writes these character classes as ``_L20``,
    ``_L20B``, ``_L11`` and ``L21``. They are public here (:data:`L20`,
    :data:`L20B`, :data:`L11`, :data:`L21`) because the test suite and the
    recogniser charset both need them; underscore-prefixed aliases are kept so
    that a reader holding the document finds the exact names it uses.
"""

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


# ---------------------------------------------------------------------------
# Plate kinds
# ---------------------------------------------------------------------------


class PlateKind(StrEnum):
    """The plate families this module can recognise.

    A kind is a *classification of the character string*, not a statement about
    the vehicle: several kinds share the same string layout, which is exactly
    why :class:`~ai.inference.normalizer.VietnamesePlateNormalizer` reports a
    list of candidates instead of a single verdict when the string is
    ambiguous (see sections 8.5 and 8.6 of the specification).

    Members:
        CAR: White or yellow plate, ``<province><letter><4-5 digits>``.
        MOTORCYCLE_NEW: Two-letter serial, issued from 15/08/2023.
        MOTORCYCLE_OLD: Letter + digit serial, still legally in circulation.
        BLUE_CAR: State-agency plate, serial restricted to 11 letters.
        BLUE_MOTORCYCLE: State-agency motorcycle, serial letter + digit 1-9.
        SPECIAL: Two-character serial codes such as ``LD``, ``DA``, ``RM``.
        DIPLOMATIC: Diplomatic/foreign plate carrying a 3-digit country code.
        MILITARY: Army plate. Recognised **only so it can be excluded**: it is
            outside the civil registration system and is never reported as a
            valid civil format.
        UNKNOWN: Nothing matched.
    """

    CAR = "car"
    MOTORCYCLE_NEW = "motorcycle_new"
    MOTORCYCLE_OLD = "motorcycle_old"
    BLUE_CAR = "blue_car"
    BLUE_MOTORCYCLE = "blue_motorcycle"
    SPECIAL = "special"
    DIPLOMATIC = "diplomatic"
    MILITARY = "military"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Province codes -- section 4 and 8.2 of the specification
# ---------------------------------------------------------------------------

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
"""The 81 province codes currently in use (Appendix of 51/2025/TT-BCA).

81 = 80 local codes + one code for the Traffic Police Department (``80``).
Validating against this set rather than ``\\d{2}`` is what rejects a plate such
as ``13A-123.45``: the code ``13`` has never been issued.

The 2025 merger of administrative units did **not** invalidate existing plates,
so a code may name a province that no longer exists as an entity. That is a
semantic concern for the reporting layer, not a format concern.
"""

UNUSED_PROVINCE_CODES: Final[frozenset[str]] = frozenset(
    {"13", "42", "44", "45", "46", "87", "91", "96"}
)
"""The 8 two-digit codes that are deliberately never issued.

Kept explicitly rather than derived, so that a consistency test can assert
``PROVINCE_CODES | UNUSED_PROVINCE_CODES`` covers exactly ``11``-``99`` minus
the codes below ``11``.
"""

_PROVINCE: Final[str] = "(?:" + "|".join(sorted(PROVINCE_CODES)) + ")"


# ---------------------------------------------------------------------------
# Serial character classes -- sections 5.3 and 8.2
# ---------------------------------------------------------------------------

L20: Final[str] = r"[A-HK-NPS-VXYZ]"
"""The 20 standard serial letters: ``A B C D E F G H K L M N P S T U V X Y Z``.

Used for the single serial letter of a car plate and for the **first** serial
letter of a motorcycle plate. Note it contains ``G`` and not ``R``.
"""

L20B: Final[str] = r"[A-FHK-NPRS-VXYZ]"
"""The 20 letters valid as the **second** serial letter of a motorcycle plate.

``A B C D E F H K L M N P R S T U V X Y Z`` -- this set contains ``R`` and does
**not** contain ``G``, the mirror image of :data:`L20`. The asymmetry is real
and consequential: ``29-AR 123.45`` is valid while ``29-AG 123.45`` is not.

.. warning::
   Sections 5.2 and 5.3 of the specification record that this list could not be
   cross-checked against the full text of Article 34 of 79/2024/TT-BCA (the
   official PDF is a scan without a text layer, and the legal portal blocks
   automated access with HTTP 403). Treat :data:`L20` and :data:`L20B` as
   well-founded hypotheses. If the full text contradicts them, only these two
   constants change -- the pattern architecture does not.
"""

L11: Final[str] = r"[A-HK-M]"
"""The 11 serial letters of blue state-agency plates: ``A``-``H``, ``K``, ``L``, ``M``."""

L21: Final[str] = r"[A-HK-NPR-VXYZ]"
"""The safe recognition charset: the 20 standard letters plus ``R``.

Rationale (section 5.2): a model whose charset is built from "20 letters" can
never predict ``R`` and will therefore fail *systematically* on every
motorcycle plate carrying ``R`` in the second serial position -- an error no
post-processing can repair, because the information is destroyed at the model
layer.
"""

# Aliases matching the constant names used in the specification document.
_L20: Final[str] = L20
_L20B: Final[str] = L20B
_L11: Final[str] = L11

EXCLUDED_LETTERS: Final[frozenset[str]] = frozenset({"I", "J", "O", "Q", "W"})
"""The 5 letters excluded from the plate system system-wide.

The document's earlier "6 excluded letters" figure (``I J O Q R W``) was
corrected: ``R`` remains valid as the second motorcycle serial letter and in
the ``RM``/``R`` trailer codes, so it is **not** excluded (section 11.3).

The exclusion of ``I``, ``O`` and ``Q`` is what makes OCR post-correction
tractable here: the candidate space at a letter position is already pruned by
the standard itself, and several confusions collapse to a single candidate.
"""

_DIGITS: Final[str] = "0123456789"
_L21_LETTERS: Final[str] = "".join(
    letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if letter not in EXCLUDED_LETTERS
)

OCR_SAFE_CHARSET: Final[str] = _DIGITS + _L21_LETTERS
"""31 characters: 10 digits + the 21 letters that can legally appear on a plate.

Use this to constrain or to audit recogniser output. It is the enumerated form
of ``0-9`` together with :data:`L21`.
"""

OCR_TRAINING_CHARSET: Final[str] = _DIGITS + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"""36 characters: the full ``0-9A-Z`` alphabet used to **train** a recogniser.

Training on 36 and constraining to 31 afterwards is a deliberate split
(section 5.2, recommendation 1 and 2): a model free to predict an illegal
character produces an observable, loggable, repairable mistake, whereas a model
architecturally unable to predict a character produces an invisible one.
"""

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
"""Special serial codes (section 5.4), in the order the pattern alternates them.

``MD`` and ``TD`` are the ASCII forms of ``MĐ`` and ``TĐ``: a Latin-charset
recogniser will practically always return ``D`` for ``Đ``, so
:func:`clean_text` folds ``Đ`` to ``D`` and only the ASCII form appears here.

Two-character codes are listed before the single-character ``R`` and ``T`` so
that the alternation prefers the longer match.
"""


# ---------------------------------------------------------------------------
# Patterns -- section 8.3
# ---------------------------------------------------------------------------

_NUM: Final[str] = r"\d{4,5}"
"""The order-number group: 5 digits today, 4 on older plates still in use."""

RE_CAR: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})" rf"(?P<serial>{L20})" rf"(?P<number>{_NUM})$"
)
"""White/yellow car plate: province + 1 serial letter + 4-5 digits.

Applies to both one-line and two-line car plates: the character string is
identical, only the physical line break differs.
"""

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
"""Motorcycle plate issued before 15/08/2023: letter + digit serial, e.g. ``29B112345``.

The serial digit runs ``1``-``9``; there is no ``0``. That small constraint is
worth a lot in practice: a ``0`` read at this position is *certainly* an OCR
error, and the correct candidate is almost always ``D`` because ``O`` and ``Q``
are not legal letters.

These plates remain legally valid and must never be dropped.
"""

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
"""State-agency car plate: serial restricted to the 11 blue-plate letters.

A negative result here is only meaningful *in the blue-plate context*:
``80N12345`` fails this pattern but is perfectly valid under :data:`RE_CAR`,
since ``N`` belongs to :data:`L20`.
"""

RE_BLUE_MOTORCYCLE: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})(?P<serial>{L11})" rf"(?P<digit>[1-9])(?P<number>{_NUM})$"
)
"""State-agency motorcycle plate: 11-letter serial + digit ``1``-``9``."""

RE_SPECIAL: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<code>{'|'.join(SPECIAL_SERIAL_CODES)})"
    rf"(?P<number>{_NUM})$"
)
"""Special serial codes: ``LD``, ``DA``, ``RM``, ``MK``, ``HC``, ``KT``, ``MD``, ...

Ambiguity warning (section 8.6): every two-letter code whose first letter is in
:data:`L20` and whose second is in :data:`L20B` also matches
:data:`RE_MOTORCYCLE_NEW` -- ``29LD12345`` is the canonical example. Unlike the
8-character ambiguity, this one **cannot** be resolved by line count, because
both are two-line plates.
"""

RE_DIPLOMATIC: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<province>{_PROVINCE})"
    rf"(?P<country>\d{{3}})"
    rf"(?P<code>NG|QT|CV|NN)"
    rf"(?P<number>\d{{2,3}})$"
)
"""Diplomatic/foreign plate: province + 3-digit country code + code + number."""

RE_MILITARY: Final[re.Pattern[str]] = re.compile(r"^(?P<unit>[A-Z]{2})(?P<number>\d{4,6})$")
"""Army plate, which starts with two letters instead of a province code.

Present **to recognise and exclude**, not to validate: army plates are outside
the civil registration system this project targets.
"""

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
"""Patterns in classification priority order (see section 8.6, resolution 1).

:data:`~PlateKind.DIPLOMATIC` comes first because its shape is unmistakable;
:data:`~PlateKind.SPECIAL` comes before the motorcycle patterns because the
special-code list is closed and rare, so a match there is almost certainly
right; :data:`~PlateKind.MILITARY` comes last because it is the
recognise-to-exclude case.

``BLUE_CAR``/``BLUE_MOTORCYCLE`` are strict subsets of ``CAR``/``MOTORCYCLE``
and are listed after them: colour, not string shape, is what actually
distinguishes a blue plate, and colour is out of scope here (section 6.4).

``CAR`` precedes ``MOTORCYCLE_OLD`` **only as a tie-break**, so that an
8-character string with no line-count hint gets the more common grouping
(``30A`` + ``123.45`` rather than ``30A1`` + ``2345``) when it is displayed.
The order is a default, not a resolution: the ambiguity flag reported by
:class:`~ai.inference.normalizer.KindDecision` stays authoritative, and at 9
characters the question does not arise because ``RE_CAR`` cannot match.
"""

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
"""Kinds that count as a valid civil plate format.

:data:`~PlateKind.MILITARY` is deliberately absent: matching ``RE_MILITARY`` is
a reason to *flag and exclude*, not a reason to report a valid format.
"""


# ---------------------------------------------------------------------------
# Position masks -- sections 8.5 and 9
# ---------------------------------------------------------------------------

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
"""Per-position type constraints, the foundation of every OCR repair rule.

``D`` = must be a digit, ``L`` = must be a letter, ``?`` = **wildcard, must be
left untouched**.

Both motorcycle styles share ``motorcycle_9``. Splitting them into
``DDLLDDDDD`` and ``DDLDDDDDD`` would force coercion at index 3 -- precisely
where section 9.4 forbids it -- and the verified consequence is destruction of
one style or the other::

    29AA12345 + 'DDLDDDDDD' -> 29A412345   breaks the new style
    29B112345 + 'DDLLDDDDD' -> 29BL12345   breaks the old style
    29AA12345 + 'DDL?DDDDD' -> 29AA12345   correct
    29B112345 + 'DDL?DDDDD' -> 29B112345   correct

Index 3 of the 9-character string is the **only** position in the whole
Vietnamese plate system where a letter and a digit are both legal (``29AA...``
versus ``29B1...``). The mask must not claim otherwise: the mask, not the
docstring, is what decides the function's behaviour.
"""

MASK_BY_LENGTH: Final[dict[int, str]] = {
    7: POSITION_MASKS["car_4"],
    8: POSITION_MASKS["car_5"],
    9: POSITION_MASKS["motorcycle_9"],
}
"""Mask selected purely by cleaned-string length (section 9.5).

The car / old-motorcycle ambiguity at 8 characters needs no alternative mask:
both readings impose the *same* type constraints (``DDLDDDDD``) and differ only
in how the groups are interpreted.
"""


# ---------------------------------------------------------------------------
# OCR confusion tables -- section 9.6
# ---------------------------------------------------------------------------

TO_DIGIT: Final[dict[str, str]] = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "J": "1",
    "L": "1",
    "Z": "2",
    "A": "4",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}
"""Table A: letter -> digit, applied only at positions the mask marks ``D``.

.. warning::
   **This table is derived from glyph-shape reasoning, not from measurement.**
   The one-star pairs of section 9.2 (notably ``L -> 1``) are weak conjectures.
   Phase 7 replaces this table with one extracted from a measured 36x36
   character-level confusion matrix, keeping only pairs whose confusion
   frequency clears a statistical threshold. Presenting the current table as a
   hypothesis to be tested is both honest and stronger than presenting it as a
   settled result.
"""

TO_LETTER: Final[dict[str, str]] = {
    "0": "D",
    "1": "L",
    "2": "Z",
    "3": "B",
    "4": "A",
    "5": "S",
    "6": "G",
    "7": "T",
    "8": "B",
}
"""Table B: digit -> letter, applied only at positions the mask marks ``L``.

**The mapping is not symmetric, and that is the central insight.** ``O -> 0``
is right, but ``0 -> O`` is *never* right, because ``O`` is not a legal serial
letter. With ``O`` and ``Q`` both excluded, ``D`` is the only homoglyph
candidate left, so the correct direction is::

    O -> 0   at a digit position
    0 -> D   at a letter position

The same warning about provenance applies as for :data:`TO_DIGIT`.
"""

_SEPARATOR_RE: Final[re.Pattern[str]] = re.compile(r"[^0-9A-Z]")
_D_STROKE_TRANSLATION: Final[dict[int, str]] = str.maketrans({"Đ": "D", "đ": "D"})


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


def clean_text(raw: str) -> str:
    """Reduce a raw OCR string to canonical alphanumeric form.

    Steps: fold ``Đ``/``đ`` to ``D``, upper-case, then delete every character
    that is not ``0``-``9`` or ``A``-``Z``.

    Separators are removed wholesale instead of being parsed, because their
    position is genuinely inconsistent (section 7.5): a car plate prints
    ``30A-123.45`` while a motorcycle prints ``29-AA`` on its upper line, and
    the printing rules of QCVN 08:2024/BCA could not be read in full. Deleting
    all separators turns that uncertainty into a safe decision rather than a
    guess.

    Args:
        raw: The unmodified OCR output; may contain spaces, dots, hyphens,
            line breaks, diacritics or noise characters.

    Returns:
        A string containing only digits and upper-case ASCII letters. Returns
        an empty string when nothing survives cleaning.

    Examples:
        >>> clean_text("30A-123.45")
        '30A12345'
        >>> clean_text("29-mđ 002.33")
        '29MD00233'
    """
    return _SEPARATOR_RE.sub("", raw.translate(_D_STROKE_TRANSLATION).upper())


def mask_for_length(length: int) -> str | None:
    """Return the position mask that applies to a cleaned string of this length.

    Args:
        length: Number of characters in the cleaned string.

    Returns:
        The mask, or ``None`` when the length is outside the plausible 7-9
        range -- in which case the string is too damaged for position-based
        repair and must fail in a controlled way (section 9.5).
    """
    return MASK_BY_LENGTH.get(length)


def apply_position_rules(text: str, mask: str) -> str:
    """Repair OCR confusions using the per-position type constraints.

    At a position the mask marks ``D``, any letter read is by definition an
    error and is mapped through :data:`TO_DIGIT`. At a position marked ``L``,
    any digit read is an error and is mapped through :data:`TO_LETTER`. At a
    position marked ``?`` **nothing happens at all** -- neither table is
    consulted (section 9.4).

    A character with no entry in the applicable table is **kept as it is**; it
    is never replaced by a placeholder. The string then simply fails the regex
    check, which is the intended controlled failure: ``3OB12E45`` becomes
    ``30B12E45``, not ``30B12?45``. The ``?`` symbol belongs to masks and never
    appears in output.

    Args:
        text: A cleaned string (digits and upper-case letters only).
        mask: A mask of the same length, built from ``D``, ``L`` and ``?``.

    Returns:
        The repaired string, or ``text`` unchanged if the lengths disagree --
        applying a mismatched mask would corrupt every position after the
        first discrepancy, so refusing is safer than realigning.

    Examples:
        >>> apply_position_rules("3OA12345", POSITION_MASKS["car_5"])
        '30A12345'
        >>> apply_position_rules("30012345", POSITION_MASKS["car_5"])
        '30D12345'
        >>> apply_position_rules("29AA12345", POSITION_MASKS["motorcycle_9"])
        '29AA12345'
    """
    if len(text) != len(mask):
        return text

    out: list[str] = []
    for char, kind in zip(text, mask, strict=True):
        if kind == MASK_WILDCARD:
            # Forbidden zone (section 9.4): a letter and a digit are both legal
            # here. Return the character untouched -- do not consult TO_DIGIT,
            # do not consult TO_LETTER. This branch is spelled out rather than
            # left to fall into `else` because the constraint is a deliberate
            # rule, not an accident of condition ordering.
            out.append(char)
        elif kind == MASK_DIGIT and char.isalpha():
            out.append(TO_DIGIT.get(char, char))
        elif kind == MASK_LETTER and char.isdigit():
            out.append(TO_LETTER.get(char, char))
        else:
            out.append(char)
    return "".join(out)
