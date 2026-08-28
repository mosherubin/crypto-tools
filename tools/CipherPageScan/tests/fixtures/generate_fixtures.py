"""
Generates small synthetic PDF fixtures for CipherPageScan's test suite, so
should_flag/ and should_not_flag/ never need real archival PDFs or binary
data committed to git. Each fixture targets a specific detection behavior
validated against real archive scans during development: grid/table OCR
segmentation (PSM 6), bidi control character stripping, the strict-majority
run requirement, and the line-adjacency requirement.

Run directly to (re)generate the fixtures:
    python generate_fixtures.py
"""

import os

import fitz
from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = os.path.dirname(__file__)
SHOULD_FLAG = os.path.join(FIXTURES_DIR, "should_flag")
SHOULD_NOT_FLAG = os.path.join(FIXTURES_DIR, "should_not_flag")
FONT_PATH = "C:/Windows/Fonts/arial.ttf"


def _image_only_pdf(pdf_path: str, lines: list, width: int = 900, height: int = 260,
                     font_size: int = 28) -> None:
    """Render lines of text to an image and embed it as an image-only PDF
    page (no text layer), forcing the detector down the OCR path."""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, font_size)
    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black", font=font)
        y += font_size + 14

    tmp_png = pdf_path + ".tmp.png"
    img.save(tmp_png)
    try:
        doc = fitz.open()
        page = doc.new_page(width=width, height=height)
        page.insert_image(fitz.Rect(0, 0, width, height), filename=tmp_png)
        doc.save(pdf_path)
        doc.close()
    finally:
        os.remove(tmp_png)


def generate_hebrew_grid():
    """Two adjacent lines of 5-letter groups, OCR-forced: exercises PSM 6
    (Tesseract's default page segmentation fragments this kind of grid into
    one word per line) and bidi control character stripping together."""
    _image_only_pdf(
        os.path.join(SHOULD_FLAG, "synthetic_hebrew_grid.pdf"),
        [
            "אבגדה וזחטי כלמנס עפצקר שתךםן",
            "הדגבא יטחזו סנמלכ רקצפע ןםךתש",
        ],
    )


def generate_digit_grid():
    """Two adjacent lines of 5-digit groups, OCR-forced: mirrors the real
    handwritten numeric telegram pattern (digits rather than letters)."""
    _image_only_pdf(
        os.path.join(SHOULD_FLAG, "synthetic_digit_grid.pdf"),
        [
            "78646 12064 24706 78019 88722",
            "73707 66035 40695 85691 25036",
        ],
    )


def generate_hebrew_prose():
    """Ordinary Hebrew prose, OCR-forced: Hebrew sentences can have a
    majority of exactly-5-letter words (unlike English/Spanish, where word
    length varies more), so this exercises the combination of purity,
    strict-majority, and adjacency needed to reject prose that a naive
    length-only check would flag. Verified offline against longest_group_run
    / line_purity (each line: run=0) before use, since a plausible-looking
    sentence can accidentally have too many medium-length words in a row --
    exactly the failure mode this fixture is meant to guard against."""
    _image_only_pdf(
        os.path.join(SHOULD_NOT_FLAG, "synthetic_hebrew_prose.pdf"),
        [
            "אני חושב שהנושא הזה חשוב מאוד לכולנו",
            "הוא לא ידע מה קרה שם באמת באותו הרגע",
            "זהו יום חשוב עבור כל אחד מאיתנו כאן",
        ],
    )


def generate_majority_strict_negative():
    """A short, mostly-garbled line where only one of three medium-length
    tokens is an actual strict 5-character group: exercises the
    strict-majority requirement (a run only counts if at least half its
    tokens are real groups, not merely the right length)."""
    _image_only_pdf(
        os.path.join(SHOULD_NOT_FLAG, "synthetic_majority_strict_negative.pdf"),
        [
            "Dear Committee, please review this letter soon.",
            "Viet stand Mean, further correspondence follows.",
            "We remain hopeful for a favorable response.",
        ],
    )


def generate_isolated_single_line():
    """A single line of genuine, cleanly-formed groups with no adjacent
    qualifying line above or below: exercises the adjacency requirement --
    a real dispatch runs across multiple lines, so an isolated line, however
    clean, is deliberately not treated as a match on its own."""
    _image_only_pdf(
        os.path.join(SHOULD_NOT_FLAG, "synthetic_isolated_single_line.pdf"),
        [
            "Dear Committee, please review the attached documents soon.",
            "XQBTP LMNOP QRSTU VWXYZ ABCDE",
            "We remain hopeful for a swift and favorable reply.",
        ],
    )


GENERATORS = [
    generate_hebrew_grid,
    generate_digit_grid,
    generate_hebrew_prose,
    generate_majority_strict_negative,
    generate_isolated_single_line,
]


def main():
    os.makedirs(SHOULD_FLAG, exist_ok=True)
    os.makedirs(SHOULD_NOT_FLAG, exist_ok=True)
    for generator in GENERATORS:
        generator()
    print(f"Generated {len(GENERATORS)} fixture PDF(s).")


if __name__ == "__main__":
    main()
