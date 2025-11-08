# tests/test_patient_details.py
from patient_details import PatientDetails

SAMPLE_ENTITIES = {
    "doctor_name": None,
    "patient_name": "Adarta Sharapova Date",
    "date": "wfil/2022",
    "patient_address": "9 tennis court, new Russia, DC\nLN\nOX",
    "medicines": [
        {"name": "Prednisone", "strength": "20 mg", "directions": "Taper 5 mg every 3 days"},
        {"name": "Lialda", "strength": "2.4 gram", "directions": "take 2 pill everyday for 1 month"}
    ],
    "refills": "2",
    "warnings": []
}

def test_patient_from_extractor_and_normalize():
    p = PatientDetails.from_extractor(SAMPLE_ENTITIES)
    assert p.patient_name == "Adarta Sharapova"
    assert p.parsed_date == "2022-01-01"
    assert "tennis court" in (p.patient_address or "").lower()
    assert isinstance(p.medicines, list) and len(p.medicines) == 2
    assert p.refills == 2
    m = p.to_model()
    assert m.parsed_date == "2022-01-01"
    assert m.patient_name == "Adarta Sharapova"
