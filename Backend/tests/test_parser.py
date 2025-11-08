# tests/test_parser.py
import json
from extract_entities_regex import PrescriptionParser

SAMPLE = """Name; Adarta Sharapova Date: wfil/2022
Address: 9 tennis court, new Russia, DC
Prednisone 20 mg
Lialda 2.4 gram
Directions:
Prednisone, Taper 5 mg every 3 days,
Lialda - take 2 pill everyday for 1 month
Refill: 2
"""

def test_parser_basic():
    p = PrescriptionParser(SAMPLE)
    out = p.parse()
    assert out['patient_name'].startswith("Adarta Sharapova")
    assert out['date'] in ("2022",) or out['date'] is not None
    assert "tennis court" in (out['patient_address'] or "").lower()
    assert isinstance(out['medicines'], list) and len(out['medicines']) >= 1
    assert out['refills'] == 2
