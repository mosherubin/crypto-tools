"""
Detects pages likely to contain enciphered/encoded text formatted as rows of
fixed-length character groups (e.g. "XQBTP LMNOP ..."), regardless of script
(Latin, digits, Hebrew, ...). Used to triage large PDF archives for pages
worth a cryptanalyst's attention.
"""

import os
import shutil
import unicodedata
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

GROUP_LENGTH = 5
GROUP_LENGTH_TOLERANCE = 1  # OCR noise merges/splits group boundaries by a character or two
MIN_TEXT_LAYER_CHARS = 20
DEFAULT_LANGS = "eng+heb"
DEFAULT_DPI = 300
DEFAULT_MIN_PURITY = 0.7
DEFAULT_PSM = 6  # "assume a single uniform block of text": Tesseract's default (3,
# fully automatic layout detection) fragments grid/table-formatted group text into
# one word per detected line, since it tries to infer columns/paragraphs


def is_group_token(token: str) -> bool:
    return len(token) == GROUP_LENGTH and token.isalnum()


def is_group_shaped(token: str) -> bool:
    """Only checks length (within GROUP_LENGTH_TOLERANCE of 5), not exact
    character content: OCR noise routinely corrupts a group's characters, or
    drops/adds one, without changing its column width."""
    return abs(len(token) - GROUP_LENGTH) <= GROUP_LENGTH_TOLERANCE


def longest_group_run(line: str) -> int:
    """Longest run of consecutive group-shaped tokens where at least half the
    run's tokens are strict group tokens (exact length 5, alnum).

    The shaped-only test tolerates OCR/handwriting noise that corrupts or
    drops/adds a character in an otherwise genuine group. But applied on its
    own, it also matches short ordinary-language phrases whose words merely
    happen to be medium-length -- e.g. OCR garbage like "Viet stand Mean,"
    scores as a run of 3 purely on token length, even though only one of
    those three ("stand") is an actual exact-5-alnum group. Requiring a
    strict-token majority within the run keeps the OCR-noise tolerance for
    genuine groups while rejecting runs that are mostly not groups at all."""
    tokens = line.split()
    best = 0
    run_start = 0
    for i in range(len(tokens) + 1):
        if i == len(tokens) or not is_group_shaped(tokens[i]):
            run = tokens[run_start:i]
            if run and sum(1 for token in run if is_group_token(token)) * 2 >= len(run):
                best = max(best, len(run))
            run_start = i + 1
    return best


def line_purity(line: str) -> float:
    """Fraction of the line's tokens that are group-shaped (length close to
    5, regardless of exact character content). Real formatted cipher rows
    stay close to 1.0 even under OCR noise, since the columnar width
    survives; ordinary prose has widely varying word lengths and is diluted
    well below that by the surrounding non-group-shaped tokens."""
    tokens = line.split()
    if not tokens:
        return 0.0
    return sum(1 for token in tokens if is_group_shaped(token)) / len(tokens)


@dataclass
class PageResult:
    page_num: int  # 1-indexed
    method: str  # "text_layer" | "ocr"
    text: str
    matched_lines: list = field(default_factory=list)  # list of (line_index, line_text, run_length)
    ambivalent_lines: list = field(default_factory=list)  # same shape: qualifying lines with no adjacent match

    @property
    def matched(self) -> bool:
        return bool(self.matched_lines)

    @property
    def ambivalent(self) -> bool:
        return bool(self.ambivalent_lines)


def scan_page_text(text: str, min_groups: int, min_lines: int, min_purity: float = DEFAULT_MIN_PURITY):
    """Returns (matches, ambivalent_lines).

    A line only counts as matched if an immediately adjacent line (either
    side) also independently qualifies. A genuine coded dispatch runs across
    multiple consecutive lines; a single isolated qualifying line -- however
    it arose -- is treated as noise rather than as evidence on its own.

    A qualifying line with no adjacent qualifying neighbor isn't just
    discarded, though: it's reported separately as "ambivalent" -- the tool
    found something structurally group-shaped but couldn't confirm it, which
    is a different, more actionable state than "found nothing at all" (e.g.
    worth a retry at higher --dpi, which might reveal a genuine neighbor the
    current OCR pass missed)."""
    lines = text.splitlines()
    runs = [longest_group_run(line) for line in lines]
    qualifies = [runs[i] >= min_groups and line_purity(lines[i]) >= min_purity for i in range(len(lines))]

    matches = []
    ambivalent_lines = []
    for i, line in enumerate(lines):
        if not qualifies[i]:
            continue
        has_adjacent = (i > 0 and qualifies[i - 1]) or (i + 1 < len(lines) and qualifies[i + 1])
        if has_adjacent:
            matches.append((i, line, runs[i]))
        else:
            ambivalent_lines.append((i, line, runs[i]))

    matches = matches if len(matches) >= min_lines else []
    return matches, ambivalent_lines


def configure_tesseract() -> None:
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
        pytesseract.pytesseract.tesseract_cmd = env_cmd
        return
    if shutil.which("tesseract"):
        return
    default_windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.isfile(default_windows_path):
        pytesseract.pytesseract.tesseract_cmd = default_windows_path


def check_tesseract_available(langs: str) -> None:
    configure_tesseract()
    try:
        available = set(pytesseract.get_languages(config=""))
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR binary not found. Install it and ensure it is on PATH "
            "(Windows build: https://github.com/UB-Mannheim/tesseract/wiki), or set "
            "the TESSERACT_CMD environment variable to the full path of tesseract.exe."
        ) from exc

    missing = [lang for lang in langs.split("+") if lang not in available]
    if missing:
        raise RuntimeError(
            f"Missing Tesseract language data: {', '.join(missing)}. "
            f"Available: {', '.join(sorted(available))}. "
            "Download the missing .traineddata files from "
            "https://github.com/tesseract-ocr/tessdata and place them in Tesseract's "
            "tessdata directory."
        )


def extract_text_layer(page: fitz.Page) -> str:
    text = page.get_text("text")
    return text if len(text.strip()) >= MIN_TEXT_LAYER_CHARS else None


def render_page_image(page: fitz.Page, dpi: int) -> Image.Image:
    zoom = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def strip_format_chars(text: str) -> str:
    """Remove invisible Unicode format characters (category Cf) -- notably the
    bidi control marks (RLM/LRM) Tesseract inserts into RTL-script OCR output.
    These are never rendered glyphs and otherwise corrupt group-length token
    checks by silently inflating a token's character count."""
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


BORDER_ARTIFACT_CHARS = "-|"


def strip_border_artifacts(text: str) -> str:
    """Remove dash and pipe characters, which routinely appear spliced into a
    word's OCR bounding box when a printed form's ruled table/cell border
    lines touch or overlap adjacent text -- corrupting a token's apparent
    length and content without reflecting anything actually printed. Applied
    per-word (not by splitting the whole line on these characters), so a
    genuine mid-word hyphen merges into one longer token rather than being
    split into two shorter ones."""
    return "".join(ch for ch in text if ch not in BORDER_ARTIFACT_CHARS)


def reconstruct_lines(ocr_data: dict) -> str:
    lines = {}
    for i, word in enumerate(ocr_data["text"]):
        word = strip_border_artifacts(strip_format_chars(word.strip()))
        if not word:
            continue
        key = (ocr_data["block_num"][i], ocr_data["par_num"][i], ocr_data["line_num"][i])
        lines.setdefault(key, []).append((ocr_data["left"][i], word))

    ordered_lines = []
    for key in sorted(lines):
        words = [word for _, word in sorted(lines[key])]
        ordered_lines.append(" ".join(words))
    return "\n".join(ordered_lines)


def ocr_page_text(page: fitz.Page, dpi: int, langs: str, psm: int = DEFAULT_PSM) -> str:
    image = render_page_image(page, dpi)
    data = pytesseract.image_to_data(image, lang=langs, config=f"--psm {psm}",
                                      output_type=pytesseract.Output.DICT)
    return reconstruct_lines(data)


def scan_page(page: fitz.Page, page_num: int, dpi: int, langs: str, min_groups: int, min_lines: int,
              min_purity: float = DEFAULT_MIN_PURITY, psm: int = DEFAULT_PSM) -> PageResult:
    text = extract_text_layer(page)
    method = "text_layer"
    if text is None:
        text = ocr_page_text(page, dpi, langs, psm)
        method = "ocr"
    matches, ambivalent_lines = scan_page_text(text, min_groups, min_lines, min_purity)
    return PageResult(page_num, method, text, matches, ambivalent_lines)


def scan_pdf(pdf_path: str, dpi: int, langs: str, min_groups: int, min_lines: int,
             stop_at_first_hit: bool, min_purity: float = DEFAULT_MIN_PURITY, psm: int = DEFAULT_PSM):
    """Yield a PageResult per page scanned. Stops after the first matched page
    when stop_at_first_hit is set, leaving later pages unscanned."""
    with fitz.open(pdf_path) as doc:
        for page_num in range(1, doc.page_count + 1):
            result = scan_page(doc[page_num - 1], page_num, dpi, langs, min_groups, min_lines, min_purity, psm)
            yield result
            if result.matched and stop_at_first_hit:
                return
