# tests/test_extract_name.py
from extract_entities_regex import PrescriptionParser

def test_get_name_with_label_and_date_on_same_line():
    txt = "Name; Adarta Sharapova Date: wfil/2022\nAddress: 9 tennis court"
    p = PrescriptionParser(txt)
    assert p.get_name() == "Adarta Sharapova"

def test_get_name_line_fallback():
    txt = "Some header\nAdarta Sharapova\nOther info"
    p = PrescriptionParser(txt)
    assert p.get_name() == "Adarta Sharapova"

def test_get_doctor_by_prefix():
    txt = "Dr. Samuel L. Jackson\nAddress: somewhere"
    p = PrescriptionParser(txt)
    assert p.get_name(doctor=True).startswith("Samuel L")

def test_get_name_hyphen_apostrophe():
    txt = "Patient: Mary-Ann O'Neill\nAddress: x"
    p = PrescriptionParser(txt)
    assert p.get_name() == "Mary-Ann O'Neill"
