# patient_details.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import re

from pydantic import BaseModel, Field, validator


@dataclass
class Medicine:
    name: str
    strength: Optional[str] = ""
    directions: Optional[str] = ""

    def normalized(self) -> "Medicine":
        name = (self.name or "").strip()
        strength = (self.strength or "").strip()
        directions = (self.directions or "").strip()
        name = re.sub(r'\s+', ' ', name)
        strength = re.sub(r'\s+', ' ', strength)
        directions = re.sub(r'\s+', ' ', directions)
        return Medicine(name=name, strength=strength, directions=directions)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "strength": self.strength, "directions": self.directions}


class PatientDetailsModel(BaseModel):
    doctor_name: Optional[str] = Field(default=None)
    patient_name: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    parsed_date: Optional[str] = Field(default=None)
    patient_address: Optional[str] = Field(default=None)
    medicines: List[Dict[str, Any]] = Field(default_factory=list)
    refills: int = Field(default=0)
    warnings: List[str] = Field(default_factory=list)

    @validator("refills", pre=True, always=True)
    def refills_must_be_int(cls, v):
        try:
            return int(v or 0)
        except Exception:
            return 0

    @validator("patient_name", pre=True, always=True)
    def normalize_name(cls, v):
        if not v:
            return None
        v = re.sub(r'\bDate\s*[:\-]?\s*$', '', v, flags=re.I).strip()
        v = re.sub(r'\s+', ' ', v).strip()
        return v


class PatientDetails:
    def __init__(self,
                 doctor_name: Optional[str] = None,
                 patient_name: Optional[str] = None,
                 date: Optional[str] = None,
                 patient_address: Optional[str] = None,
                 medicines: Optional[List[Dict[str, Any]]] = None,
                 refills: int = 0,
                 warnings: Optional[List[str]] = None):
        self.doctor_name = doctor_name
        self.patient_name = patient_name
        self.date = date
        self.parsed_date = None
        self.patient_address = patient_address
        self.medicines = [Medicine(**m) if isinstance(m, dict) else Medicine(m) for m in (medicines or [])]
        self.refills = int(refills or 0)
        self.warnings = warnings or []
        self._normalize()

    def _normalize(self):
        if self.patient_name:
            self.patient_name = re.sub(r'\s+', ' ', self.patient_name).strip()
            self.patient_name = re.sub(r'\bDate\b.*$', '', self.patient_name, flags=re.I).strip()

        if self.patient_address:
            self.patient_address = re.sub(r'\s+', ' ', self.patient_address).strip()
            self.patient_address = self.patient_address.rstrip('.,|')

        self.medicines = [m.normalized() for m in self.medicines]

        if self.date:
            self.parsed_date = self._try_parse_date(self.date)

    @staticmethod
    def _try_parse_date(dt_str: str) -> Optional[str]:
        if not dt_str:
            return None
        dt_str = dt_str.strip()
        patterns = [
            "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
            "%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"
        ]
        for p in patterns:
            try:
                d = datetime.strptime(dt_str, p)
                return d.date().isoformat()
            except Exception:
                continue
        y = re.search(r'\b(19|20)\d{2}\b', dt_str)
        if y:
            return f"{y.group(0)}-01-01"
        return None

    @classmethod
    def from_extractor(cls, entities: Dict[str, Any]) -> "PatientDetails":
        doctor = entities.get("doctor_name") or entities.get("doctor")
        patient = entities.get("patient_name") or entities.get("name")
        date = entities.get("date")
        address = entities.get("patient_address") or entities.get("address")
        medicines = entities.get("medicines") or []
        meds_out = []
        for m in medicines:
            if isinstance(m, str):
                meds_out.append({"name": m, "strength": "", "directions": ""})
            elif isinstance(m, dict):
                meds_out.append({"name": m.get("name") or "", "strength": m.get("strength") or "", "directions": m.get("directions") or ""})
            else:
                meds_out.append({"name": str(m), "strength": "", "directions": ""})
        refills = entities.get("refills") or entities.get("refill") or 0
        warnings = entities.get("warnings") or []
        return cls(doctor_name=doctor,
                   patient_name=patient,
                   date=date,
                   patient_address=address,
                   medicines=meds_out,
                   refills=refills,
                   warnings=warnings)

    def to_model(self) -> PatientDetailsModel:
        model = PatientDetailsModel(
            doctor_name=self.doctor_name,
            patient_name=self.patient_name,
            date=self.date,
            parsed_date=self.parsed_date,
            patient_address=self.patient_address,
            medicines=[m.to_dict() for m in self.medicines],
            refills=self.refills,
            warnings=self.warnings
        )
        return model

    def to_dict(self) -> Dict[str, Any]:
        return self.to_model().dict()
