---
name: readme-to-latex-pdf
description: Convert README.md or Markdown reports into LaTeX and polished PDF deliverables, especially Chinese academic-style reports. Use when Codex needs to generate .tex/.pdf from Markdown, fix messy section numbering, set Chinese/English fonts, handle Pandoc/LaTeX tooling, or validate PDF rendering with pdffonts, pdftotext, and pdftoppm.
---

# README To LaTeX PDF

## Core Rule

Produce both `.tex` and `.pdf`, then validate the PDF visually and structurally before reporting completion. Do not trust "compiled successfully" alone.

Use `scripts/md_to_pdf.sh` for the standard workflow:

```bash
/home/xuke/.codex/skills/readme-to-latex-pdf/scripts/md_to_pdf.sh README.md output/pdf
```

If tools are unpacked locally rather than installed globally, pass them with environment variables:

```bash
LD_LIBRARY_PATH=/path/to/libs \
PANDOC=/path/to/pandoc \
PANDOC_DATA_DIR=/path/to/pandoc/data \
TECTONIC=/path/to/tectonic \
/home/xuke/.codex/skills/readme-to-latex-pdf/scripts/md_to_pdf.sh README.md output/pdf
```

The script writes:

- `output/pdf/README_report.tex`
- `output/pdf/README_report.pdf`
- `output/pdf/render/page-*.png`
- `output/pdf/validation/`

## Workflow

1. Inspect the Markdown heading structure.
2. If the first line is a document title like `# Project Report`, make it the PDF title, remove it from the body, and shift headings up by one level.
3. If headings already contain manual numbers like `## 1. Background` and `### 1.1 Task`, do not use Pandoc `--number-sections`.
4. Generate LaTeX with `ctexart`, `A4`, `12pt`, `1in` margins, and a custom CJK header.
5. Compile with `tectonic` when available, otherwise `xelatex`.
6. Validate with `pdffonts`, `pdftotext`, and rendered PNG pages.
7. Open representative PNGs with image inspection before final response.

## Heading Fixes

Avoid double numbering such as:

```text
1 TAAC2026 CVR ...
1.3  1. Project Background
1.3.1  1.1 Task
```

For README-style reports:

- Treat the top `# ...` as document title, not a numbered section.
- Keep `摘要` and `引言` unnumbered.
- Keep existing manual numbering in body headings.
- Use `--shift-heading-level-by=-1` after removing the top title.
- Do not pass `--number-sections` when the Markdown already has manual numbers.

Expected structure:

```text
Title
目录
摘要
引言
1. 项目背景与任务定义
  1.1 任务形式
  1.2 数据基本构成
2. 官方模板理解
  2.1 模板模型
```

## Font Policy

For Chinese academic-style reports:

- Body Chinese: 小四 via `\zihao{-4}`.
- English and digits: Times New Roman if installed; otherwise Liberation Serif.
- Chinese font priority:
  1. `SimSun` only if it is actually installed or provided by the user.
  2. `AR PL UMing CN` as the stable Linux fallback closest to Song/Ming style.
  3. `Noto Serif CJK SC` only as a display-safe fallback when UMing is unavailable.

Do not download Microsoft `simsun.ttc` from random websites. It is commonly redistributed without permission. If the user provides their own `simsun.ttc` or the system has `SimSun`, use it.

Avoid FandolSong for final deliverables unless you verify the target viewer renders it correctly. In this project it looked close to Song visually, but `pdffonts` showed `uni no`, and one PDF viewer displayed only English/digits, making the document appear scrambled.

## Validation Checklist

Run these checks for every final PDF:

```bash
pdffonts output/pdf/README_report.pdf
pdftotext output/pdf/README_report.pdf - | sed -n '1,80p'
pdftoppm -png -f 1 -l 4 output/pdf/README_report.pdf output/pdf/render/page
```

Check `pdffonts`:

- CJK font should be embedded: `emb yes`.
- Prefer CJK `uni yes`; this avoids missing Chinese, broken copy/search, and viewer-specific failures.
- If CJK font is `FandolSong-*` and `uni no`, do not deliver without testing in the user's viewer.

Inspect rendered PNGs:

- Page 1: title, table of contents, section numbering.
- Page 2 or 3: `摘要` / `引言` text, Chinese glyphs, line breaks.
- A later page with tables/code blocks.
- Last page, to catch clipped content or bad page transitions.

## Common Problems

`pandoc: default.latex not found`

- Install or extract `pandoc-data`, or set Pandoc `--data-dir` to the extracted data directory.

`pandoc: libcmark-gfm... not found`

- Add the extracted library directory to `LD_LIBRARY_PATH`, or install the missing runtime packages.

Chinese does not render

- Inspect `pdffonts`.
- Switch from problematic CJK fonts to `AR PL UMing CN` or a user-provided `SimSun`.
- Rebuild `.tex` after changing the header; Pandoc copies header contents into the `.tex`.

PDF compiles but content looks scrambled

- Suspect missing CJK glyph rendering in the viewer.
- Check if only English/digits are visible.
- Replace CJK font and confirm `pdffonts` reports `uni yes`.

Numbering is messy

- Remove the top README title from body.
- Do not combine manual numbered headings with `--number-sections`.
- Use `--shift-heading-level-by=-1` to make `摘要` / `引言` and `1. ...` top-level sections.

## Final Response

Report the PDF and `.tex` paths, summarize font choices, and explicitly mention validation results. If true SimSun or Times New Roman are unavailable, say which fallback was used.
