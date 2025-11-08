# tests/test_doc_extractor.py
from src.parsers.doc_extractor import DocumentExtractor

SAMPLE_TEXT = """===== PAGE 1 =====
Name: Adarta Sharapova Date: wfil/2022
Address: 9 tennis court, new Russia, DC
Prednisone 20 mg
Lialda 2.4 gram
Directions:
Prednisone, Taper 5 mg every 3 days,
Lialda - take 2 pill everyday for 1 month
Refill: 2
"""

def test_doc_extractor_basic():
    de = DocumentExtractor()
    out = de.extract_from_text(SAMPLE_TEXT)
    assert isinstance(out, dict)
    assert "entities" in out
    assert "patient" in out
    # patient name should be present either in patient model or entities
    patient = out["patient"] or out["entities"]
    name = patient.get("patient_name") or patient.get("name") or patient.get("patient")
    assert name is not None
