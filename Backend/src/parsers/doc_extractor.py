"""
DocumentExtractor: orchestrates the various parser classes
(eg PrescriptionParser and PatientDetails) and returns a single
normalized dict with: entities, patient, parsed_date, warnings.
"""
from typing import Dict, Any, Optional, List
import traceback

# Try imports from likely locations
PrescriptionParser = None
PatientDetails = None

try:
    # package-style import if you refactored under src/
    from src.parsers.prescription_parser import PrescriptionParser  # type: ignore
except Exception:
    PrescriptionParser = None

if PrescriptionParser is None:
    try:
        # fallback to the original module name
        from extract_entities_regex import PrescriptionParser  # type: ignore
    except Exception:
        PrescriptionParser = None

try:
    from src.models.patient_details import PatientDetails  # type: ignore
except Exception:
    PatientDetails = None

if PatientDetails is None:
    try:
        from patient_details import PatientDetails  # type: ignore
    except Exception:
        PatientDetails = None


class DocumentExtractor:
    def __init__(self):
        self.warnings: List[str] = []

    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Run the prescription parser (class or function) and optionally
        normalize via PatientDetails if available.
        Returns a dict with keys: entities, patient, warnings, parsed_date.
        """
        self.warnings = []
        entities: Dict[str, Any] = {}
        patient_obj: Optional[Dict[str, Any]] = None
        parsed_date: Optional[str] = None

        # Run prescription parser
        try:
            if PrescriptionParser is not None:
                # support class-based parser
                entities = PrescriptionParser(text).parse() or {}
            else:
                # try function fallback name
                try:
                    from extract_entities_regex import extract_entities  # type: ignore
                    entities = extract_entities(text) or {}
                except Exception:
                    entities = {}
                    self.warnings.append("No prescription parser available.")
        except Exception:
            self.warnings.append("PrescriptionParser threw an exception; see server logs.")
            print("=== PRESCRIPTION PARSER TRACE ===")
            print(traceback.format_exc())
            entities = {}

        # Normalize patient details if class exists
        if PatientDetails is not None:
            try:
                patient = PatientDetails.from_extractor(entities or {})
                patient_obj = patient.to_model().dict()
                parsed_date = patient_obj.get("parsed_date") or patient_obj.get("date")
            except Exception:
                patient_obj = None
                self.warnings.append("PatientDetails normalization failed; see server logs.")
                print("=== PATIENTDETAILS TRACE ===")
                print(traceback.format_exc())
        else:
            parsed_date = entities.get("date")

        return {
            "entities": entities or {},
            "patient": patient_obj,
            "warnings": self.warnings,
            "parsed_date": parsed_date,
        }
