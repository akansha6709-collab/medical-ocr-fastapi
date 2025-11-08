# app.py - Final (production-friendly, env-driven)
import os
import traceback
import tempfile
import json
import uuid
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# OCR / image libs
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import cv2
import numpy as np

# -----------------------
# Tesseract / Poppler setup
# - Use environment variables when provided
#   - TESSERACT_CMD  -> full path to tesseract executable (optional)
#   - POPPLER_PATH   -> directory containing pdftoppm (optional on Windows)
# -----------------------
if os.environ.get("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
# If not provided, assume tesseract is on PATH (Dockerfile / system install should ensure that)

# -----------------------
# Try to import extractor(s)
# Prefer DocumentExtractor (src.parsers.doc_extractor) if present,
# otherwise try prescription parser class or function names.
# All imports are best-effort; failing to import is non-fatal.
# -----------------------
DocumentExtractor = None
PrescriptionParser = None
extract_entities_func = None
PatientDetails = None

try:
    from src.parsers.doc_extractor import DocumentExtractor  # type: ignore
except Exception:
    DocumentExtractor = None

# PrescriptionParser class (common)
if DocumentExtractor is None:
    try:
        from src.parsers.prescription_parser import PrescriptionParser  # type: ignore
    except Exception:
        PrescriptionParser = None
    try:
        # fallback to top-level file name used in earlier exercises
        from extract_entities_regex import PrescriptionParser as PrescriptionParser2  # type: ignore
        if PrescriptionParser is None:
            PrescriptionParser = PrescriptionParser2
    except Exception:
        pass

# function-style extractors
try:
    from src.parsers.prescription_parser import extract_entities_from_ocr_text as extract_entities_func  # type: ignore
except Exception:
    extract_entities_func = None

if extract_entities_func is None:
    try:
        from extract_entities_regex import extract_entities as extract_entities_func  # type: ignore
    except Exception:
        extract_entities_func = None

# PatientDetails normalizer (optional)
try:
    from src.models.patient_details import PatientDetails  # type: ignore
except Exception:
    try:
        from patient_details import PatientDetails  # type: ignore
    except Exception:
        PatientDetails = None

# -----------------------
# Helpers: poppler/tesseract env, pdf->images, preprocessing, ocr
# -----------------------
def set_external_binaries() -> Optional[str]:
    """
    Read POPPLER_PATH (dir with pdftoppm) and TESSERACT_CMD env vars.
    Return poppler_path (or None).
    """
    poppler_path = os.environ.get("POPPLER_PATH")
    # TESSERACT_CMD applied earlier at import time; re-read if needed
    tcmd = os.environ.get("TESSERACT_CMD")
    if tcmd:
        pytesseract.pytesseract.tesseract_cmd = tcmd
    return poppler_path

def pdf_to_images(pdf_path: str, poppler_path: Optional[str] = None, dpi: int = 300):
    if poppler_path:
        return convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    return convert_from_path(pdf_path, dpi=dpi)

def preprocess_image_for_ocr(pil_image: Image.Image) -> Image.Image:
    arr = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    denoised = cv2.medianBlur(gray, 3)
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=9
    )
    return Image.fromarray(thresh)

def ocr_pages(pages: List[Image.Image]) -> str:
    out = []
    for i, p in enumerate(pages, start=1):
        proc = preprocess_image_for_ocr(p)
        txt = pytesseract.image_to_string(proc, config="--oem 3 --psm 6")
        out.append(f"===== PAGE {i} =====\n{txt}\n")
    return "\n".join(out)

def run_extractor_on_text(ocr_text: str) -> Dict[str, Any]:
    """
    Try DocumentExtractor, PrescriptionParser (class), or extract function.
    Always return a dict (maybe empty).
    """
    try:
        if DocumentExtractor is not None:
            try:
                de = DocumentExtractor()
                # DocumentExtractor.extract_from_text() typically returns dict with keys "entities","patient",...
                res = de.extract_from_text(ocr_text)
                # prefer nested 'entities' if present
                if isinstance(res, dict) and "entities" in res:
                    return res.get("entities", {}) or {}
                if isinstance(res, dict):
                    return res
                return {}
            except Exception:
                print("=== DocumentExtractor error ===")
                print(traceback.format_exc())
                return {}
        if PrescriptionParser is not None:
            try:
                p = PrescriptionParser(ocr_text)
                if hasattr(p, "parse"):
                    return p.parse() or {}
                return {}
            except Exception:
                print("=== PrescriptionParser error ===")
                print(traceback.format_exc())
                return {}
        if extract_entities_func is not None:
            try:
                return extract_entities_func(ocr_text) or {}
            except Exception:
                print("=== extract_entities_func error ===")
                print(traceback.format_exc())
                return {}
    except Exception:
        print("=== Unknown extractor error ===")
        print(traceback.format_exc())
        return {}
    return {}

# -----------------------
# FastAPI application
# -----------------------
app = FastAPI(title="Prescription OCR API")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# /extract endpoint
# -----------------------
@app.post("/extract")
async def extract_prescription(file: UploadFile = File(...)) -> Dict[str, Any]:
    poppler_path = set_external_binaries()
    warnings: List[str] = []

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    try:
        with tempfile.TemporaryDirectory() as td:
            tmp_pdf = os.path.join(td, "upload.pdf")
            # read file content
            content = await file.read()
            with open(tmp_pdf, "wb") as fw:
                fw.write(content)

            # pdf -> images
            pages = []
            try:
                pages = pdf_to_images(tmp_pdf, poppler_path=poppler_path, dpi=300)
            except Exception:
                warnings.append("PDF->image conversion failed (poppler may be missing). OCR skipped.")
                print("=== PDF->IMAGE ERROR ===")
                print(traceback.format_exc())

            # OCR
            ocr_text = ""
            if pages:
                try:
                    ocr_text = ocr_pages(pages)
                except Exception:
                    warnings.append("OCR failed (tesseract may be missing). Using placeholder text.")
                    print("=== OCR ERROR ===")
                    print(traceback.format_exc())
                    ocr_text = "### OCR_FAILED ###\n"
            else:
                ocr_text = "### NO_PAGES ###\n"

            # run extractor
            entities = run_extractor_on_text(ocr_text) or {}

            # patient normalization if available
            patient_obj = None
            if PatientDetails is not None:
                try:
                    patient = PatientDetails.from_extractor(entities or {})
                    patient_obj = patient.to_model().dict()
                except Exception:
                    warnings.append("PatientDetails normalization failed.")
                    print("=== PATIENT DETAILS ERROR ===")
                    print(traceback.format_exc())

            result = {"text": ocr_text, "entities": entities, "patient": patient_obj, "warnings": warnings}
            return JSONResponse(status_code=200, content=result)

    except Exception:
        print("=== SERVER ERROR ===")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error — see server logs.")

# -----------------------
# Storage endpoints
# -----------------------
STORE_FILE = "stored_extractions.jsonl"

class MedicineModel(BaseModel):
    name: str = Field(default="")
    strength: Optional[str] = Field(default="")
    directions: Optional[str] = Field(default="")

class ExtractedEntityModel(BaseModel):
    doctor_name: Optional[str] = Field(default=None)
    patient_name: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    patient_address: Optional[str] = Field(default=None)
    medicines: List[MedicineModel] = Field(default_factory=list)
    refills: Optional[int] = Field(default=0)
    warnings: Optional[List[str]] = Field(default_factory=list)

@app.post("/store")
async def store_extraction(item: ExtractedEntityModel):
    rec = item.dict()
    rec["_id"] = str(uuid.uuid4())
    rec["_ts"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    os.makedirs(os.path.dirname(STORE_FILE) or ".", exist_ok=True)
    with open(STORE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"status": "ok", "id": rec["_id"]}

@app.get("/list")
def list_saved(limit: int = 50) -> Dict[str, Any]:
    out: List[Dict[str, Any]] = []
    if not os.path.exists(STORE_FILE):
        return {"count": 0, "results": []}
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            for ln in lines[-limit:][::-1]:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    continue
    except Exception:
        print("=== READ STORE FAILED ===")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to read store.")
    return {"count": len(out), "results": out}

@app.get("/health")
def health():
    return {"status": "ok"}
