"""Generate editable DOCX, Markdown, and plain text from one resume source."""
import json
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "resume.json").read_text())
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
STEM = "Raymond_Xu_Resume"


def paragraphs(data):
    result = [("name", data["name"])]
    result += [("contact", line) for line in data["contact"]]
    result += [("heading", "Summary"), ("body", data["summary"])]
    result += [("heading", "Skills")]
    result += [("body", line) for line in data["skills"]]
    result += [("heading", "Experience")]
    for job in data["experience"]:
        result.append(("job", f'{job["employer"]} | {job["title"]}'))
        result.append(("date", job["dates"]))
        result += [("bullet", text) for text in job["bullets"]]
    result += [("heading", "Projects")]
    for project in data["projects"]:
        result.append(("project", f'{project["name"]} | {project["url"]}'))
        result.append(("bullet", project["description"]))
    result += [("heading", "Education")]
    result += [("body", line) for line in data["education"]]
    return result


def build():
    doc = Document()
    # The runtime's default template can carry a blue rule in the Title style.
    # Strip paragraph borders so the exported resume stays plain black text.
    for element in (doc.element, doc.styles.element):
        for border in list(element.iter(qn("w:pBdr"))):
            border.getparent().remove(border)
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.48)
    section.bottom_margin = Inches(0.48)
    section.left_margin = section.right_margin = Inches(0.62)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(2)
    normal.paragraph_format.line_spacing = 1.0
    normal.paragraph_format.widow_control = True
    for style_name in ("Title", "Heading 1", "List Bullet"):
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), "Arial")
    title = doc.styles["Title"]
    title.font.size = Pt(22)
    title.font.bold = True
    title.paragraph_format.space_after = Pt(3)
    heading = doc.styles["Heading 1"]
    heading.font.size = Pt(10.5)
    heading.font.bold = True
    heading.paragraph_format.space_before = Pt(7)
    heading.paragraph_format.space_after = Pt(3)
    heading.paragraph_format.keep_with_next = True
    bullet = doc.styles["List Bullet"]
    bullet.font.size = Pt(10)
    bullet.paragraph_format.left_indent = Inches(0.12)
    bullet.paragraph_format.first_line_indent = Inches(-0.12)
    bullet.paragraph_format.space_after = Pt(2)
    # Use a real list with a plain hyphen in Arial; no Symbol-font glyphs.
    for abstract in doc.part.numbering_part.element.findall(qn("w:abstractNum")):
        for lvl in abstract.findall(qn("w:lvl")):
            fmt = lvl.find(qn("w:numFmt"))
            if fmt is not None and fmt.get(qn("w:val")) == "bullet":
                lvl.find(qn("w:lvlText")).set(qn("w:val"), "-")
                props = lvl.find(qn("w:rPr"))
                if props is None:
                    props = OxmlElement("w:rPr")
                    lvl.append(props)
                fonts = props.find(qn("w:rFonts"))
                if fonts is None:
                    fonts = OxmlElement("w:rFonts")
                    props.append(fonts)
                for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
                    fonts.set(qn(f"w:{attr}"), "Arial")
    doc.core_properties.title = "Raymond Xu Resume"
    doc.core_properties.author = "Raymond Xu"
    doc.core_properties.subject = "Applied AI and Machine Learning"
    doc.core_properties.keywords = ""
    doc.core_properties.comments = ""
    doc.core_properties.last_modified_by = "Raymond Xu"
    text_lines, md_lines = [], []
    for kind, text in paragraphs(DATA):
        style = {"name": "Title", "heading": "Heading 1", "bullet": "List Bullet"}.get(kind)
        p = doc.add_paragraph(text, style=style)
        p.paragraph_format.keep_together = True
        if kind in {"name", "contact", "job", "date", "project"}:
            p.paragraph_format.keep_with_next = True
        if kind == "contact":
            p.paragraph_format.space_after = Pt(1)
            for run in p.runs:
                run.font.size = Pt(9.5)
        if kind in {"job", "project"}:
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(0)
            for run in p.runs:
                run.bold = True
        if kind == "date":
            p.paragraph_format.space_after = Pt(2)
            for run in p.runs:
                run.font.size = Pt(9.5)
        prefix = "- " if kind == "bullet" else ""
        if kind in {"heading", "job", "project"}:
            text_lines.append("")
            md_lines.append("")
        text_lines.append(prefix + text)
        if kind == "name":
            md_lines.append("# " + text)
        elif kind == "heading":
            md_lines.extend(["## " + text, ""])
        elif kind in {"job", "project"}:
            md_lines.append("**" + text + "**")
        else:
            md_lines.append(prefix + text)
    doc.save(OUT / f"{STEM}.docx")
    (OUT / f"{STEM}.txt").write_text("\n".join(text_lines) + "\n")
    (ROOT / "resume.md").write_text("\n".join(md_lines) + "\n")
    print(f"Built {OUT / (STEM + '.docx')}")


if __name__ == "__main__":
    build()
