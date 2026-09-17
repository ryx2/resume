"""Generate a LaTeX resume, plain text, and Markdown from the factual source."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "resume.json").read_text())
OUT = ROOT / "output"
STEM = "Raymond_Xu_Resume"


def escape(text):
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "|": r"\textbar{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def contact_tex(line):
    parts = []
    for part in line.split(" | "):
        label, separator, address = part.partition(": ")
        prefix = label + separator if separator else ""
        address = address if separator else part
        url = "mailto:" + address if "@" in address else "https://" + address if ".com" in address else None
        if url and url.startswith("https://") and "/" not in address:
            url += "/"
        parts.append(escape(prefix) + r"\href{" + url + "}{" + escape(address) + "}" if url else escape(part))
    return r"\enspace\textbar{}\enspace{}".join(parts)


def paragraphs(data):
    """Expected PDF reading order, including the visual role/employer hierarchy."""
    result = [("name", data["name"])]
    result += [("contact", line) for line in data["contact"]]
    result += [("body", data["summary"]), ("heading", "Skills")]
    result += [("body", line) for line in data["skills"]]
    result += [("heading", "Experience")]
    for job in data["experience"]:
        result.append(("job", job["title"]))
        result.append(("employer", job["employer"] + " " + job["dates"]))
        result += [("bullet", text) for text in job["bullets"]]
    result += [("heading", "Education")]
    for line in data["education"]:
        employer, degree, year = line.split(" | ")
        result.append(("body", f"{employer} | {degree} | {year}"))
    return result


def build(compile_pdf=False):
    OUT.mkdir(exist_ok=True)
    content = [r"\begin{center}", r"{\fontsize{27}{29}\selectfont " + escape(DATA["name"]) + r"}\par\vspace{3pt}"]
    content += [r"{\small " + contact_tex(line) + r"}\par" for line in DATA["contact"]]
    content += [r"\end{center}", r"\vspace{1pt}", escape(DATA["summary"]) + r"\par"]
    content.append(r"\ResumeSection{Skills}")
    for line in DATA["skills"]:
        label, text = line.split(": ", 1)
        content.append(r"\textbf{" + escape(label) + ":} " + escape(text) + r"\par")
    content.append(r"\ResumeSection{Experience}")
    for job in DATA["experience"]:
        args = [job["title"], job["employer"], job["dates"]]
        content.append(r"\ResumeRole" + "".join("{" + escape(arg) + "}" for arg in args))
        content.append(r"\begin{ResumeItems}")
        content += [r"\item " + escape(text) for text in job["bullets"]]
        content.append(r"\end{ResumeItems}")
    content.append(r"\ResumeSection{Education}")
    for line in DATA["education"]:
        employer, degree, year = line.split(" | ")
        content.append(r"\textbf{" + escape(employer) + r"} \textbar{} " + escape(degree) + r" \textbar{} " + escape(year) + r"\par")
    template = (ROOT / "template.tex").read_text()
    tex = ROOT / f"{STEM}.tex"
    tex.write_text(template.replace("%%CONTENT%%", "\n".join(content)))
    text_lines, md_lines = [], []
    for kind, text in paragraphs(DATA):
        if kind in {"heading", "job"}:
            text_lines.append("")
            md_lines.append("")
        prefix = "- " if kind == "bullet" else ""
        text_lines.append(prefix + text)
        if kind == "name":
            md_lines.extend(["# " + text, ""])
        elif kind == "heading":
            md_lines.extend(["## " + text, ""])
        elif kind == "job":
            md_lines.append("**" + text + "**")
        elif kind == "employer":
            md_lines.extend([text, ""])
        else:
            md_lines.append(prefix + text)
            if kind in {"contact", "body"}:
                md_lines.append("")
    (OUT / f"{STEM}.txt").write_text("\n".join(text_lines) + "\n")
    (ROOT / "resume.md").write_text("\n".join(md_lines).rstrip() + "\n")
    print(f"Generated {tex}")
    if compile_pdf:
        compiler = shutil.which("tectonic")
        if not compiler:
            raise SystemExit("Install Tectonic (brew install tectonic), or compile the .tex with another LaTeX engine.")
        subprocess.run([compiler, "--keep-logs", "--outdir", str(OUT), str(tex)], cwd=ROOT, check=True)
        print(f"Compiled {OUT / (STEM + '.pdf')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true", help="Compile the generated LaTeX with Tectonic")
    build(parser.parse_args().compile)
