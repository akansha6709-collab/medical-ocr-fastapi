# extract_entities_regex.py
import re
from typing import List, Dict, Optional

# --- helper functions (cleaning, regexes) ---
def clean_ocr_text(raw: str) -> str:
    """
    Clean OCR text while preserving line breaks (important for line-aware parsing).
    """
    if not raw:
        return ""
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('—', '-').replace('–', '-')
    text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E]', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    lines = [ln.strip() for ln in text.split('\n')]
    lines = [ln for ln in lines if ln]
    if not lines:
        return ""
    fixed_lines = []
    for ln in lines:
        ln = re.sub(r'(\d+)\s+(me|m g|mgm)\b', r'\1 mg', ln, flags=re.I)
        ln = re.sub(r'(?<=\s)[A-Za-z](?=\s)', ' ', ln)
        ln = re.sub(r'\s+', ' ', ln).strip()
        fixed_lines.append(ln)
    return '\n'.join(fixed_lines)


# small compiled regexes used by class methods
_DOCTOR_RE = re.compile(r'\b(?:Dr\.?|Doctor|Physician)[:\s\-]*([A-Z][A-Za-z\.\s\-]{1,60})', re.I)
_PATIENT_RE = re.compile(r'\b(?:Patient|Name)[:;\-\s]*([A-Z][A-Za-z\.\s\-]{1,60})', re.I)
_DATE_RE = re.compile(
    r'(?P<d>(?:\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b)|(?:\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b)|(?:\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b))',
    re.I
)
_REFILL_RE = re.compile(r'\bRefill[s]?\s*[:\-]?\s*([0-9]+)', re.I)

UNIT_WORD_RE = re.compile(r'\b(?:mg|g|gram|grams|ml|mcg|tablet|tab|capsule|drop|patch)\b', re.I)
DIRECTION_WORD_RE = re.compile(r'\b(?:take|every|daily|once|twice|before|after|with|apply|taper|inhale|use|for)\b', re.I)

_MED_LINE_RE = re.compile(
    r'^(?P<name>[A-Za-z][A-Za-z0-9\-\(\)\/\. ]{2,80}?)'
    r'(?:\s+[,|-]?\s*)?(?P<strength>\d{1,3}(?:\.\d+)?\s*(?:mg|g|gram|grams|ml|mcg)?)?'
    r'(?:\s*[,|-]?\s*)(?P<extra>.*)$',
    re.I
)


# ----------------------
# The class
# ----------------------
class PrescriptionParser:
    def __init__(self, text: str):
        self.raw = text or ""
        cleaned = clean_ocr_text(self.raw)
        self.text = cleaned
        self.lines = [ln.strip() for ln in cleaned.split('\n') if ln.strip()]

    def parse(self) -> Dict:
        return {
            "doctor_name": self.get_name(doctor=True),
            "patient_name": self.get_name(doctor=False),
            "date": self.get_date(),
            "patient_address": self.get_address(),
            "medicines": self.get_medicines(),
            "refills": self.get_refills(),
            "warnings": []
        }

    def get_name(self, doctor: bool = False) -> Optional[str]:
        if doctor:
            m = re.search(r'\b(?:Dr\.?|Doctor|Physician)[:\s\-]*([A-Z][A-Za-z\.\'\- ]{1,60})', self.text, re.I)
            if m:
                candidate = m.group(1).strip()
                candidate = re.sub(r'[,:;\|\-]+$', '', candidate).strip()
                return re.sub(r'\s+', ' ', candidate)
        m = re.search(r'\b(?:Patient|Name)[:;\-\s]*([A-Z][A-Za-z\.\'\-\s]{1,60}?)(?=\s+Date\b|$|\n)', self.text, re.I)
        if m:
            name = m.group(1).strip()
            name = re.sub(r'[,:;\|\-]+$', '', name).strip()
            return re.sub(r'\s+', ' ', name)
        for ln in self.lines:
            if re.search(r'\b(Address|Date|Phone|Dr|Physician|Directions|Refill|Amount|Page)\b', ln, re.I):
                continue
            ln_clean = re.sub(r'^(?:Name|Patient)[:;\-\s]*', '', ln, flags=re.I).strip()
            words = ln_clean.split()
            if 2 <= len(words) <= 4:
                good = True
                for w in words:
                    if not re.match(r"^[A-Z][A-Za-z'\-\.]{1,}$", w):
                        good = False
                        break
                if good:
                    candidate = re.sub(r'[,:;\|]+$', '', ln_clean).strip()
                    return re.sub(r'\s+', ' ', candidate)
        m2 = re.search(r'\bName\b[^\nA-Za-z0-9]{0,6}([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){1,3})', self.text)
        if m2:
            return re.sub(r'\s+', ' ', m2.group(1).strip())
        return None

    def get_date(self) -> Optional[str]:
        m = _DATE_RE.search(self.text)
        if m:
            return m.group('d').strip()
        m2 = re.search(r'Date[:;\s]*([^\n]{0,30})', self.text, re.I)
        if m2:
            y = re.search(r'\b(19|20)\d{2}\b', m2.group(1))
            if y:
                return y.group(0)
        y2 = re.search(r'\b(19|20)\d{2}\b', self.text)
        return y2.group(0) if y2 else None

    def get_refills(self) -> int:
        m = _REFILL_RE.search(self.text)
        try:
            return int(m.group(1)) if m else 0
        except:
            return 0

    def get_address(self) -> Optional[str]:
        addr_lines = []
        found = False
        for i, ln in enumerate(self.lines):
            if not found:
                if re.search(r'\bAddress[:\s\-]', ln, re.I):
                    part = re.split(r'Address[:\s\-]*', ln, flags=re.I)[-1].strip()
                    if part:
                        addr_lines.append(part)
                    found = True
            else:
                if UNIT_WORD_RE.search(ln) or DIRECTION_WORD_RE.search(ln) or re.search(r'\bRefill\b', ln, re.I):
                    break
                if re.search(r'[A-Z][a-z]{2,}\s+\d', ln):
                    break
                addr_lines.append(ln)
        if addr_lines:
            a = ' '.join(addr_lines)
            a = re.sub(r'\s+,', ',', a)
            return a.strip().rstrip('.,')
        m = re.search(r'\bAddress[:\s]*([A-Za-z0-9,\.\s\-]{10,120})', self.text, re.I)
        return m.group(1).strip().rstrip('.,') if m else None

    def get_medicines(self) -> List[Dict]:
        """
        Improved medicine extraction:
        - Detects medicine name + strength accurately.
        - Handles directions across lines.
        """
        meds = []

        pair_re = re.compile(
            r'([A-Za-z][A-Za-z0-9\-\(\)\/\.\s]{2,80}?)'
            r'\s*[,:-]?\s*'
            r'(\d{1,3}(?:\.\d+)?\s*(?:mg|g|gram|grams|ml|mcg))',
            re.I
        )
        name_only_re = re.compile(r'\b([A-Za-z][A-Za-z\-\']{2,60})\b')

        for idx, ln in enumerate(self.lines):
            if re.search(r'\b(Address|Name|Date|Phone|Refill|Page|Directions)\b', ln, re.I):
                if ln.strip().lower().startswith("directions"):
                    continue

            line_meds = []

            for m in pair_re.finditer(ln):
                name = (m.group(1) or "").strip()
                strength = (m.group(2) or "").strip()
                post = ln[m.end():].strip(" ,;:-")
                direction = ""
                if DIRECTION_WORD_RE.search(post):
                    direction = post
                else:
                    for j in range(1, 3):
                        if idx + j < len(self.lines):
                            nxt = self.lines[idx + j]
                            if DIRECTION_WORD_RE.search(nxt):
                                direction = nxt
                                break
                name = re.sub(r'[^A-Za-z0-9\-\(\)\/\.\' ]+', '', name).strip()
                if len(re.sub(r'[^A-Za-z]', '', name)) < 3:
                    continue
                line_meds.append({"name": name, "strength": strength, "directions": direction.strip()})

            if line_meds:
                meds.extend(line_meds)
                continue

            if UNIT_WORD_RE.search(ln) or re.search(r'\b\d', ln) or re.search(r'\b[A-Za-z]{6,}\b', ln):
                parts = re.split(r'[,;\-:]\s*', ln)
                candidate = parts[0].strip()
                candidate = re.sub(r'\b\d[\d\.]*\s*(?:mg|g|gram|grams|ml|mcg)\b', '', candidate, flags=re.I).strip()
                m2 = name_only_re.search(candidate)
                if m2:
                    name = m2.group(1).strip()
                    direction = ""
                    post = ln[len(candidate):].strip(" ,;:-")
                    if DIRECTION_WORD_RE.search(post):
                        direction = post
                    else:
                        for j in range(1, 3):
                            if idx + j < len(self.lines):
                                nxt = self.lines[idx + j]
                                if DIRECTION_WORD_RE.search(nxt):
                                    direction = nxt
                                    break
                    meds.append({"name": name, "strength": "", "directions": direction.strip()})

        seen = set()
        out = []
        for m in meds:
            key = (m["name"].lower(), (m.get("strength") or "").lower())
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "name": m["name"],
                "strength": m.get("strength", ""),
                "directions": m.get("directions", "")
            })

        return out


# Backwards compatibility wrapper (app may import extract_entities)
def extract_entities(text: str) -> Dict:
    return PrescriptionParser(text).parse()


# optional debug runner
if __name__ == "__main__":
    sample = """Name; Adarta Sharapova Date: wfil/2022
    Address: 9 tennis court, new Russia, DC
    Prednisone 20 me
    Lialda 2.4 gram
    Directions:
    Prednisone, Taper 5 mg every 3 days,
    Lialda - take 2 pill everyday for 1 month
    Refill: 2
    """
    import json
    print(json.dumps(PrescriptionParser(sample).parse(), indent=2))
