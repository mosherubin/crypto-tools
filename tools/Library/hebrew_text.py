"""
Hebrew-specific text normalization for cryptanalysis tools that treat the
Hebrew alphabet as 22 letters. Final forms are positional/typographic
variants of their base letter, not distinct cryptographic units, so they are
folded to the base letter before any statistical analysis.
"""

_FINAL_TO_BASE = {
    'ך': 'כ',  # ך -> כ
    'ם': 'מ',  # ם -> מ
    'ן': 'נ',  # ן -> נ
    'ף': 'פ',  # ף -> פ
    'ץ': 'צ',  # ץ -> צ
}

_TRANSLATION = str.maketrans(_FINAL_TO_BASE)


def normalize_finals(text: str) -> str:
    return text.translate(_TRANSLATION)
