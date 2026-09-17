# Raymond Xu Resume

The current resume is built with LaTeX in [`2026_09`](2026_09), using the centered header, section rules, and right-aligned dates from the older resume. Older versions remain in their original dated directories.

- [PDF](2026_09/output/Raymond_Xu_Resume.pdf)
- [LaTeX source](2026_09/Raymond_Xu_Resume.tex)
- [Plain text](2026_09/output/Raymond_Xu_Resume.txt)
- [Readable source](2026_09/resume.md)
- [Structured source](2026_09/resume.json)

The September 2026 version is a general AI engineering resume suitable for further tailoring toward applied AI, forward deployed engineering, senior machine learning, or founding engineer roles. Recent ventures are grouped under RayXC. Career facts come from the supplied LinkedIn history, portfolio, previous resume, project documentation, and direct clarifications.

## Editing and rebuilding

Edit `2026_09/resume.json` for content and `2026_09/template.tex` for formatting. The generator uses only Python's standard library and compiles the PDF with Tectonic:

```sh
brew install tectonic
uv run 2026_09/build_resume.py --compile
```

The generated `2026_09/Raymond_Xu_Resume.tex` is a self-contained LaTeX document. It can be edited and compiled directly with XeLaTeX, including in Overleaf. Rebuilding from JSON overwrites direct edits to the generated `.tex`. The previous Word layout is retained under `2026_09/archive/`.

With Poppler (`pdftotext`) installed, validate the final PDF:

```sh
uv run --with pypdf --with pdfplumber 2026_09/check_resume.py
pdftoppm -scale-to 2000 -png 2026_09/output/Raymond_Xu_Resume.pdf 2026_09/qa/page
```

The checker compares all text against the source in order using Poppler, pypdf, and pdfplumber; checks embedded fonts and Unicode maps; checks page size/count and margins; and verifies the small file size. It also confirms the removed Projects section stays absent. QA output is stored locally under the ignored `2026_09/qa/` directory. Visually inspect the final rendered page after every content or formatting change.

## Automated parsing

The resume uses a single column, standard section headings, selectable text, and contact details in normal document flow. Dates use ordinary paragraphs, not layout tables. It contains no photo, icons, text boxes, or hidden keywords. This follows [Greenhouse's parsing guidance](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse) and [Workday's resume API guidelines](https://developer.workday.com/documentation/GUID-f07adb7f-630e-42a2-9de9-a39652e34ec5-enHYPHENus/ResumeRESTAPI).

Local text-extraction checks are not a commercial ATS test or a ranking score. Review the application system's parsed employer, title, date, education, and contact fields when applying, and tailor truthful keywords to each job description.
