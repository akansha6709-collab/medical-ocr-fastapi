# ocr_from_image.py
from PIL import Image
import pytesseract
import sys

# If tesseract.exe is NOT on PATH, set this to your install path:
# Example (most common): r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_image(image_path: str, out_txt: str = "thresholded_text.txt"):
    # Use a reasonable page segmentation mode for a single block of text (psm 6).
    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(Image.open(image_path), config=config)
    print("=== OCR output (start) ===\n")
    print(text)
    print("\n=== OCR output (end) ===\n")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote OCR text to: {out_txt}")

if __name__ == "__main__":
    # default filename
    img = "thresholded.png"
    if len(sys.argv) > 1:
        img = sys.argv[1]
    ocr_image(img)
