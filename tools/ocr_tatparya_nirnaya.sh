#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_PDF="${ROOT_DIR}/Sri Bhagavata Tatparya Nirnaya.pdf"
OUTPUT_DIR="${ROOT_DIR}/backend/data/ocr"
OUTPUT_PDF="${OUTPUT_DIR}/Sri_Bhagavata_Tatparya_Nirnaya_OCR.pdf"
OUTPUT_TEXT="${OUTPUT_DIR}/Sri_Bhagavata_Tatparya_Nirnaya_OCR.txt"

mkdir -p "${OUTPUT_DIR}"

if ! command -v ocrmypdf >/dev/null 2>&1; then
  echo "ocrmypdf is required. Install with: brew install ocrmypdf tesseract-lang expat" >&2
  exit 1
fi

if [[ ! -f "${SOURCE_PDF}" ]]; then
  echo "Missing source PDF: ${SOURCE_PDF}" >&2
  exit 1
fi

export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib:${DYLD_LIBRARY_PATH:-}"

ocrmypdf \
  -l san+hin+eng \
  --force-ocr \
  --deskew \
  --rotate-pages \
  --jobs "${OCR_JOBS:-6}" \
  --optimize 1 \
  --sidecar "${OUTPUT_TEXT}" \
  "${SOURCE_PDF}" \
  "${OUTPUT_PDF}"

ls -lh "${OUTPUT_PDF}" "${OUTPUT_TEXT}"
