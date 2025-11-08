from extract_entities_regex import PrescriptionParser

SAMPLE = """Dr. John Doe
Phone: (000)-141-2222
Name: Adarta Sharapova Date: wfil/2022
Address: 9 tennis court, new Russia, DC
Prednisone 20 mg
Lialda 2.4 gram
Directions:
Prednisone, Taper 5 mg every 3 days,
Lialda - take 2 pill everyday for 1 month
Refill: 2
"""

def test_doctor_name():
    p = PrescriptionParser(SAMPLE)
    assert p.get_name(doctor=True) == "John Doe"

def test_patient_name():
    p = PrescriptionParser(SAMPLE)
    assert p.get_name() == "Adarta Sharapova"

def test_date_extraction():
    p = PrescriptionParser(SAMPLE)
    assert "2022" in p.get_date()

def test_address_extraction():
    p = PrescriptionParser(SAMPLE)
    addr = p.get_address()
    assert "tennis court" in addr.lower()
    assert "russia" in addr.lower()

def test_refills_extraction():
    p = PrescriptionParser(SAMPLE)
    assert p.get_refills() == 2

def test_medicine_detection():
    p = PrescriptionParser(SAMPLE)
    meds = p.get_medicines()
    names = [m["name"].lower() for m in meds]
    assert "prednisone" in names
    assert "lialda" in names
