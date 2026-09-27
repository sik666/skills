#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  md_to_pdf.sh INPUT.md OUTPUT_DIR [OUTPUT_BASENAME]

Converts a README-style Markdown report into LaTeX and PDF.

Outputs:
  OUTPUT_DIR/OUTPUT_BASENAME.tex
  OUTPUT_DIR/OUTPUT_BASENAME.pdf
  OUTPUT_DIR/render/page-*.png
  OUTPUT_DIR/validation/pdffonts.txt
  OUTPUT_DIR/validation/pdftotext_head.txt

Defaults:
  OUTPUT_BASENAME=README_report
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage >&2
  exit 2
fi

INPUT=$1
OUTDIR=$2
BASENAME=${3:-README_report}

if [[ ! -f "$INPUT" ]]; then
  echo "Input Markdown not found: $INPUT" >&2
  exit 1
fi

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    return 1
  fi
}

PANDOC_BIN=${PANDOC:-pandoc}
PANDOC_DATA_DIR=${PANDOC_DATA_DIR:-}
TECTONIC_BIN=${TECTONIC:-tectonic}
XELATEX_BIN=${XELATEX:-xelatex}

need_cmd "$PANDOC_BIN"

if command -v "$TECTONIC_BIN" >/dev/null 2>&1; then
  PDF_ENGINE=("$TECTONIC_BIN")
elif command -v "$XELATEX_BIN" >/dev/null 2>&1; then
  PDF_ENGINE=("$XELATEX_BIN" -interaction=nonstopmode)
else
  echo "Required PDF engine not found: install tectonic or xelatex." >&2
  exit 1
fi

mkdir -p "$OUTDIR" "$OUTDIR/render" "$OUTDIR/validation"

SRC="$OUTDIR/${BASENAME}.source.md"
HEADER="$OUTDIR/${BASENAME}_cjk_header.tex"
TEX="$OUTDIR/${BASENAME}.tex"
PDF="$OUTDIR/${BASENAME}.pdf"

TITLE=$(awk '/^# / {sub(/^# /, ""); print; exit}' "$INPUT")
if [[ -z "$TITLE" ]]; then
  TITLE=$(basename "$INPUT" .md)
  cp "$INPUT" "$SRC"
  SHIFT_OPT=()
else
  sed '1{/^# /d;}' "$INPUT" > "$SRC"
  SHIFT_OPT=(--shift-heading-level-by=-1)
fi

cat > "$HEADER" <<'HEADER'
\usepackage{xeCJK}
\IfFontExistsTF{Times New Roman}{
  \setmainfont{Times New Roman}
}{
  \setmainfont{Liberation Serif}
}
\IfFontExistsTF{SimSun}{
  \setCJKmainfont{SimSun}
  \setCJKsansfont{SimSun}
}{
  \IfFontExistsTF{AR PL UMing CN}{
    \setCJKmainfont{AR PL UMing CN}
    \setCJKsansfont{AR PL UMing CN}
  }{
    \setCJKmainfont{Noto Serif CJK SC}
    \setCJKsansfont{Noto Sans CJK SC}
  }
}
\IfFontExistsTF{Noto Sans CJK SC}{
  \setCJKmonofont{Noto Sans CJK SC}
}{
  \setCJKmonofont{AR PL UMing CN}
}
\AtBeginDocument{\zihao{-4}\linespread{1.25}\selectfont}
HEADER

PANDOC_DATA_OPT=()
if [[ -n "$PANDOC_DATA_DIR" ]]; then
  PANDOC_DATA_OPT=(--data-dir="$PANDOC_DATA_DIR")
fi

"$PANDOC_BIN" "${PANDOC_DATA_OPT[@]}" "$SRC" \
  "${SHIFT_OPT[@]}" \
  -s --toc \
  -V "title=$TITLE" \
  -V documentclass=ctexart \
  -V fontsize=12pt \
  -V classoption=fontset=none \
  -V geometry:a4paper \
  -V geometry:margin=1in \
  -H "$HEADER" \
  -o "$TEX"

(
  cd "$OUTDIR"
  rm -f "${BASENAME}.pdf" "${BASENAME}.aux" "${BASENAME}.log" "${BASENAME}.toc"
  "${PDF_ENGINE[@]}" "${BASENAME}.tex"
  if [[ "${PDF_ENGINE[0]}" == "xelatex" ]]; then
    "${PDF_ENGINE[@]}" "${BASENAME}.tex" >/dev/null
  fi
)

if command -v pdffonts >/dev/null 2>&1; then
  pdffonts "$PDF" > "$OUTDIR/validation/pdffonts.txt"
  if awk 'NR > 2 && ($1 ~ /(Fandol|Song|UMing|NotoSerif|NotoSans|SimSun)/) && $7 == "no" {bad=1} END {exit bad ? 0 : 1}' "$OUTDIR/validation/pdffonts.txt"; then
    echo "Warning: a CJK-like font may have uni=no. Inspect validation/pdffonts.txt and test viewer rendering." >&2
  fi
fi

if command -v pdftotext >/dev/null 2>&1; then
  pdftotext "$PDF" - | sed -n '1,100p' > "$OUTDIR/validation/pdftotext_head.txt"
fi

if command -v pdftoppm >/dev/null 2>&1; then
  rm -f "$OUTDIR"/render/page-*.png
  PAGES=1
  if command -v pdfinfo >/dev/null 2>&1; then
    PAGES=$(pdfinfo "$PDF" | awk '/^Pages:/ {print $2}')
  fi
  LAST=$PAGES
  FIRST_END=$(( PAGES < 4 ? PAGES : 4 ))
  pdftoppm -png -f 1 -l "$FIRST_END" "$PDF" "$OUTDIR/render/page"
  if [[ "$PAGES" -gt 4 ]]; then
    START=$(( PAGES > 3 ? PAGES - 2 : 1 ))
    pdftoppm -png -f "$START" -l "$LAST" "$PDF" "$OUTDIR/render/page"
  fi
fi

echo "Wrote: $TEX"
echo "Wrote: $PDF"
echo "Validation: $OUTDIR/validation"
echo "Rendered PNGs: $OUTDIR/render"
