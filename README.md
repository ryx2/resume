# Raymond Xu Resume

The current resume is in [`2026_09`](2026_09). Older LaTeX versions remain in their original dated directories.

- [PDF](2026_09/output/Raymond_Xu_Resume.pdf)
- [Editable Word document](2026_09/output/Raymond_Xu_Resume.docx)
- [Plain text](2026_09/output/Raymond_Xu_Resume.txt)
- [Readable source](2026_09/resume.md)
- [Structured source](2026_09/resume.json)

The September 2026 version is a general AI engineering resume suitable for further tailoring toward applied AI, forward deployed engineering, senior machine learning, or founding engineer roles. Recent ventures are grouped under RayXC. Career facts come from the supplied LinkedIn history, portfolio, previous resume, project documentation, and direct clarifications.

## Editing and rebuilding

Edit `2026_09/resume.json`; it is the single source for the DOCX, Markdown, and plain-text outputs. `build_resume.py` uses `python-docx`:

```sh
uv run --with python-docx 2026_09/build_resume.py
```

Export the resulting Word file to PDF with LibreOffice or Word, keeping text selectable and preserving the one-page layout. In Codex, use the documents skill's bundled `render_docx.py` with `--emit_pdf`; it also renders page images for visual review. Copy the generated PDF into `2026_09/output/` before validation.

With Poppler (`pdftotext`) installed, validate both final artifacts:

```sh
uv run --with python-docx --with pypdf --with pdfplumber 2026_09/check_resume.py
```

The checker compares every paragraph against the source in order through DOCX and three independent PDF extraction libraries (Poppler, pypdf, pdfplumber), checks page size/count, excludes text boxes and layout tables, checks margins, and verifies small file sizes. QA output is stored locally under the ignored `2026_09/qa/` directory. Visually inspect the final rendered page after every content or formatting change.

## Automated parsing

The resume uses a single column, standard section headings, real document paragraphs, readable text, and contact details in the body. It contains no photo, icons, text boxes, layout tables, or hidden keywords. This follows [Greenhouse's parsing guidance](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse) and [Workday's resume API guidelines](https://developer.workday.com/documentation/GUID-f07adb7f-630e-42a2-9de9-a39652e34ec5-enHYPHENus/ResumeRESTAPI).

Local text-extraction checks are not a commercial ATS test or a ranking score. Review the application system's parsed employer, title, date, education, and contact fields when applying, and tailor truthful keywords to each job description.
