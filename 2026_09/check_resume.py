"""Validate artifact structure and complete text extraction; not an ATS score."""
import json
import re
import shutil
import subprocess
import unicodedata

import pdfplumber
from pypdf import PdfReader

from build_resume import OUT, ROOT, STEM


def without_comments(tex):
    """Remove TeX comments while retaining escaped percent signs."""
    result = []
    i = 0
    while i < len(tex):
        if tex[i] == "\\":
            result.append(tex[i:i + 2])
            i += 2
        elif tex[i] == "%":
            end = tex.find("\n", i)
            i = len(tex) if end < 0 else end + 1
        else:
            result.append(tex[i])
            i += 1
    return "".join(result)


def display_text(source):
    """Read the small set of display macros used in this resume's body.

    Unknown commands fail explicitly so a future formatting change cannot
    silently remove expected content from the extraction check.
    """
    def group(text, start):
        while start < len(text) and text[start].isspace():
            start += 1
        if start >= len(text) or text[start] != "{":
            raise ValueError(f"Expected LaTeX argument near {text[start:start + 40]!r}")
        depth, i = 1, start + 1
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            depth += (text[i] == "{") - (text[i] == "}")
            if depth == 0:
                return text[start + 1:i], i + 1
            i += 1
        raise ValueError("Unclosed LaTeX argument")

    symbols = {"textbar": "|", "textbackslash": "\\", "textasciitilde": "~",
               "textasciicircum": "^", "textbullet": "\u2022",
               **{char: char for char in "%$&#_{}"}}
    spaces = {"par", "item", "enspace", "quad", "qquad", "hfill", "\\", " "}
    styles = {"small", "selectfont", "bfseries", "itshape", "upshape", "nopagebreak"}
    wrappers = {"textbf", "textit", "emph", "underline", "ResumeSection"}

    def render(text):
        result, i = [], 0
        while i < len(text):
            if text[i] == "{":
                value, i = group(text, i)
                result.append(render(value))
            elif text[i] == "\\":
                match = re.match(r"\\([A-Za-z]+|.)", text[i:])
                if not match:
                    raise ValueError("Incomplete LaTeX command")
                command = match[1]
                i += match.end()
                if command in symbols:
                    result.append(symbols[command])
                elif command in spaces:
                    result.append("\n" if command in {"par", "item"} else " ")
                elif command in styles:
                    pass
                elif command in wrappers:
                    value, i = group(text, i)
                    result.append("\n" + render(value) + "\n" if command == "ResumeSection" else render(value))
                elif command in {"href", "ResumeRole", "fontsize", "vspace", "hspace", "begin", "end"}:
                    count = {"href": 2, "ResumeRole": 3, "fontsize": 2}.get(command, 1)
                    args = []
                    for _ in range(count):
                        value, i = group(text, i)
                        args.append(value)
                    if command == "href":
                        result.append(render(args[1]))
                    elif command == "ResumeRole":
                        result.append("\n" + " ".join(render(arg) for arg in args) + "\n")
                    elif command in {"begin", "end"}:
                        if args[0] not in {"center", "ResumeItems"}:
                            raise ValueError(f"Unsupported resume environment: {args[0]}")
                        result.append("\n")
                else:
                    raise ValueError(f"Unsupported resume command: \\{command}")
            else:
                result.append(" " if text[i] == "~" else text[i])
                i += 1
        return "".join(result)

    body = source.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]
    return render(body)


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
    tex = without_comments((ROOT / f"{STEM}.tex").read_text())
    expected_text = normalize(display_text(tex))
    report = {"scope": "Local artifact and extraction checks; no commercial ATS was run.", "checks": {}}

    def require(name, condition):
        report["checks"][name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    require("no_columns_or_layout_tables", not re.search(r"\\begin\{(?:tabular\*?|multicols|paracol|minipage)\}|\\twocolumn", tex))
    require("projects_section_removed", not re.search(r"\\ResumeSection\s*\{\s*Projects\s*\}", tex))
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
    report["source"] = f"{STEM}.tex"
    report["pages"] = len(reader.pages)
    (qa / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    check()
