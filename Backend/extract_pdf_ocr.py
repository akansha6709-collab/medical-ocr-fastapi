"""
extract_pdf_ocr.py

Usage:
    python extract_pdf_ocr.py pre_1.pdf pre_2.pdf
Produces:
    pre_1.txt, pre_2.txt (one .txt per input PDF)
Notes:
 - Set POPPLER_BIN to your Poppler bin folder (where pdftoppm.exe lives).
 - Set TESSERACT_CMD to your tesseract.exe path.
"""

import sys
import os
from pdf2image import convert_from_path
import pytesseract
import numpy as np
import cv2

# ---------- CONFIG: adjust only if your install locations differ ----------
POPPLER_BIN = r"C:\poppler\poppler-25.07.0\Library\bin"                    # Poppler bin path
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"             # Tesseract exe path
DPI = 300                                                                   # conversion DPI: 200-300 recommended
# --------------------------------------------------------------------------

# Ensure pytesseract uses the correct tesseract executable
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def preprocess_pil_image(pil_img):
    """
    Convert PIL image to OpenCV grayscale and apply preprocessing:
      - Convert to grayscale
      - Bilateral filter to reduce noise while preserving edges
      - Adaptive threshold to get clean binary text
      - Median blur to remove small artifacts
    Returns the OpenCV image ready for Tesseract.
    """
    img = np.array(pil_img.convert("RGB"))           # PIL -> RGB numpy
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)       # match OpenCV BGR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Optional: improve contrast by histogram equalization for some scans
    # gray = cv2.equalizeHist(gray)

    # Bilateral filter keeps edges, reduces noise
    gray = cv2.bilateralFilter(gray, d=7, sigmaColor=75, sigmaSpace=75)

    # Adaptive threshold (handles uneven lighting)
    processed = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=35,
        C=11
    )

    # Remove small salt-and-pepper noise
    processed = cv2.medianBlur(processed, ksize=3)

    return processed


def ocr_pdf(pdf_path: str, poppler_path: str = POPPLER_BIN, dpi: int = DPI) -> str:
    """
    Convert PDF -> images using Poppler, preprocess each page and run Tesseract.
    Returns the concatenated text for all pages.
    """
    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    out_text = []

    for i, page in enumerate(pages, start=1):
        out_text.append(f"\n===== PAGE {i} =====\n")
        try:
            proc_img = preprocess_pil_image(page)
            # psm 6 assumes a block of text; change to 4/7/11 for different layouts
            cfg = "--oem 3 --psm 6"
            text = pytesseract.image_to_string(proc_img, config=cfg, lang="eng")
            out_text.append(text)
        except Exception as e:
            out_text.append(f"[ERROR on page {i}: {e}]\n")

    return "".join(out_text)


def main(argv):
    if len(argv) < 2:
        print("Usage: python extract_pdf_ocr.py file1.pdf file2.pdf ...")
        sys.exit(1)

    pdf_files = argv[1:]

    for pdf in pdf_files:
        if not os.path.exists(pdf):
            print(f"[SKIP] Not found: {pdf}")
            continue

        print(f"[INFO] OCR: {pdf}")
        try:
            text = ocr_pdf(pdf)
            out_file = os.path.splitext(pdf)[0] + ".txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[OK] Wrote: {out_file}")
        except Exception as e:
            print(f"[FAIL] {pdf}: {e}")


if __name__ == "__main__":
    main(sys.argv)
