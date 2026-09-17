"""Validate artifact structure and complete text extraction; not an ATS score."""
import json
import re
import shutil
import subprocess
import unicodedata

import pdfplumber
from pypdf import PdfReader

from build_resume import DATA, OUT, ROOT, STEM, paragraphs


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    # LaTeX's typographic apostrophes preserve the same words as source ASCII.
    text = text.translate(str.maketrans({"\u2018": "'", "\u2019": "'"}))
    text = re.sub(r"(?m)^\s*[-\u2022]\s+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def check():
    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    pdf = OUT / f"{STEM}.pdf"
    expected = [text for _, text in paragraphs(DATA)]
    expected_text = normalize("\n".join(expected))
    report = {"scope": "Local artifact and extraction checks; no commercial ATS was run.", "checks": {}}

    def require(name, condition):
        report["checks"][name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    tex = (ROOT / f"{STEM}.tex").read_text()
    require("no_columns_or_layout_tables", not re.search(r"\\begin\{(?:tabular\*?|multicols|paracol|minipage)\}|\\twocolumn", tex))
    require("projects_section_removed", "Projects" not in [t for k, t in paragraphs(DATA) if k == "heading"])
    reader = PdfReader(pdf)
    require("pdf_one_letter_page", len(reader.pages) == 1 and abs(float(reader.pages[0].mediabox.width) - 612) < 1 and abs(float(reader.pages[0].mediabox.height) - 792) < 1)
    require("pdf_not_encrypted", not reader.is_encrypted)
    require("pdf_below_2_5_MB", pdf.stat().st_size < 2_500_000)
    extracted = {"pypdf": "\n".join(page.extract_text() for page in reader.pages)}
    fonts = []
    for page in reader.pages:
        for reference in page["/Resources"]["/Font"].values():
            font = reference.get_object()
            descriptor_font = font["/DescendantFonts"][0].get_object() if "/DescendantFonts" in font else font
            descriptor = descriptor_font.get("/FontDescriptor")
            descriptor = descriptor.get_object() if descriptor else {}
            fonts.append({"name": str(font.get("/BaseFont")), "unicode": "/ToUnicode" in font,
                          "embedded": any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))})
    require("all_fonts_embedded_with_unicode_maps", bool(fonts) and all(f["embedded"] and f["unicode"] for f in fonts))
    report["fonts"] = fonts
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("pdftotext is required for independent PDF extraction checks")
    for label, args in [("poppler", []), ("poppler_layout", ["-layout"])]:
        extracted[label] = subprocess.check_output([pdftotext, *args, str(pdf), "-"], text=True)
    with pdfplumber.open(pdf) as parsed:
        extracted["pdfplumber"] = "\n".join(page.extract_text() for page in parsed.pages)
        require("text_stays_inside_page_margins", all(
            c["x0"] >= 30 and c["x1"] <= page.width - 30 and c["top"] >= 25 and c["bottom"] <= page.height - 25
            for page in parsed.pages for c in page.chars if c["text"].strip()
        ))
        require("no_raster_images", all(not page.images for page in parsed.pages))
    for label, text in extracted.items():
        (qa / f"{label}.txt").write_text(text)
        require(f"{label}_all_content_in_source_order", normalize(text) == expected_text)
        require(f"{label}_no_replacement_characters", "\ufffd" not in text and "\u0000" not in text)
    report["files"] = {pdf.name: {"bytes": pdf.stat().st_size}}
    report["paragraphs"] = len(expected)
    report["pages"] = len(reader.pages)
    (qa / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    check()
