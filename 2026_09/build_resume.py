"""Compile the editable LaTeX resume and extract its PDF text."""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
STEM = "Raymond_Xu_Resume"


def build():
    tex = ROOT / f"{STEM}.tex"
    if not tex.is_file():
        raise SystemExit(f"LaTeX source not found: {tex}")
    compiler = shutil.which("tectonic")
    pdftotext = shutil.which("pdftotext")
    if not compiler or not pdftotext:
        raise SystemExit("Install Tectonic and Poppler: brew install tectonic poppler")
    OUT.mkdir(exist_ok=True)
    subprocess.run([compiler, "--keep-logs", "--outdir", str(OUT), str(tex)], cwd=ROOT, check=True)
    pdf = OUT / f"{STEM}.pdf"
    text = OUT / f"{STEM}.txt"
    subprocess.run([pdftotext, "-nopgbrk", str(pdf), str(text)], check=True)
    print(f"Compiled {pdf}")
    print(f"Extracted {text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true", help="Accepted for compatibility; compilation always runs")
    parser.parse_args()
    build()
