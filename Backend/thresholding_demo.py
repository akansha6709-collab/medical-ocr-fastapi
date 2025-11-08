import cv2
from pdf2image import convert_from_path
import os

# Convert first page of PDF to an image
pdf_path = "pre_1.pdf"
print(f"[INFO] Converting {pdf_path} to image...")

pages = convert_from_path(pdf_path, dpi=300)
image_path = "pre_1_page.png"
pages[0].save(image_path, "PNG")

print(f"[OK] Saved first page as {image_path}")

# Load the image in grayscale
img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

# Check if image loaded successfully
if img is None:
    print("[ERROR] Could not load image. Check path or permissions.")
    exit(1)

# Preprocess + adaptive threshold (better for uneven lighting / stains)
blur = cv2.medianBlur(img, 3)   # reduce small noise; try kernel 3 or 5
thresh = cv2.adaptiveThreshold(
    blur, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    21,   # blockSize (odd). Try 11,15,21,31 if needed.
    10    # C subtracted from mean. Try values 5..20.
)


# Save output images instead of displaying them (no GUI required)
cv2.imwrite("original_gray.png", img)
cv2.imwrite("thresholded.png", thresh)

print("[OK] Saved output images: original_gray.png and thresholded.png")

# Optional: confirm file existence
for f in ["original_gray.png", "thresholded.png"]:
    if os.path.exists(f):
        print(f"[INFO] File ready -> {f}")
    else:
        print(f"[WARNING] File not created -> {f}")
