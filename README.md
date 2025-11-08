# 🧾 Prescription OCR (FastAPI + Tesseract + Docker)

A full-stack medical document extraction system that reads **prescription PDFs**, performs **OCR (Optical Character Recognition)** using **Tesseract**, and extracts structured patient data like name, contact, and diagnosis — all powered by **FastAPI backend** and a lightweight **HTML + JavaScript frontend**.

This project demonstrates a modular full-stack setup using FastAPI, Tesseract, and Docker, maintaining a clean separation between UI and REST API layers.

---

## ✅ Features
- Upload medical prescriptions (PDF)
- Extract key details:  
  - 🧍 Patient name  
  - 📞 Phone number  
  - 💊 Medical problems  
  - 💉 Vaccination info  
- Fast, accurate OCR with Tesseract + OpenCV  
- REST API built with FastAPI  
- Simple frontend for file uploads  
- Dockerized backend for easy deployment  
- JSON response for integration into other systems  

---
![demo_ui png](https://github.com/user-attachments/assets/1d1770a0-1a13-4434-b385-5b18493e872b)


## 🧱 Architecture
medical-ocr-fastapi/
│
├── Backend
│ ├── app.py # FastAPI main app + routes
│ ├── src/
│ │ ├── ocr_utils.py # OCR and preprocessing logic
│ │ ├── extract_text.py # PDF → Text extraction
│ │ └── parser.py # Data extraction from text
│ └── tests/
│ └── test_ocr.py
│
├── Frontend
│ ├── index.html # File upload UI
│ ├── script.js # Calls FastAPI OCR endpoint
│ └── style.css # Basic layout and styling
│
├── requirements.txt
└── README.md

yaml
Copy code

---

## 🧠 OCR Flow
1. Upload PDF via frontend (`index.html`)  
2. JavaScript sends file to FastAPI endpoint `/extract_from_doc`  
3. Backend extracts text using `pdf2image + pytesseract`  
4. Parsed JSON returned:
```json
{
  "patient_name": "John Doe",
  "phone_number": "9876543210",
  "medical_problems": ["Fever", "Cough"],
  "hepatitis_b_vaccination": "No"
}
⚙️ Setup Instructions
1️⃣ Clone Repo
bash
Copy code
git clone https://github.com/akansha6709-collab/medical-ocr-fastapi.git
cd medical-ocr-fastapi
2️⃣ Create Virtual Environment
bash
Copy code
python -m venv venv
venv\Scripts\activate
3️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Start FastAPI Server
bash
Copy code
cd Backend
uvicorn app: app --reload
Backend runs on → http://127.0.0.1:8000

5️⃣ Start Frontend
bash
Copy code
cd Frontend
python -m http.server 5500
Frontend runs on → http://127.0.0.1:5500/index.html

📡 API Example
Endpoint: POST /extract_from_doc

Parameter	Type	Description
file_format	string	e.g., "pdf"
file	file	Prescription document

Response Example:

json
Copy code
{
  "patient_name": "Kathy Crawford",
  "phone_number": "(737) 988-0851",
  "medical_problems": null,
  "hepatitis_b_vaccination": "No"
}
🧪 Testing
Run tests:

bash
Copy code
pytest
🧰 Troubleshooting
Issue	Fix
❌ “Network / Fetch error: Failed to fetch.”	Ensure both backend (:8000) and frontend (:5500) are running
❌ “Tesseract not found.d”	Add Tesseract to the system PATH
❌ “CORS error”	Enable CORS in FastAPI using CORSMiddleware

🧩 Tech Stack
Layer	Technology
Frontend	HTML, CSS, JavaScript
Backend	FastAPI (Python 3.10+)
OCR	Tesseract, OpenCV, pdf2image
Containerization	Docker
Testing	Pytest

🚀 Future Roadmap
Multi-page PDF handling

AI-based prescription field classification

Frontend UI improvements

Deploy to AWS / Render using Docker

👩‍💻 Author
Akansha Singh
📧 akansha6709@example.com
🔗 GitHub: akansha6709-collab

yaml
Copy code

---

✅ After pasting this:
1. Save the file.  
2. Run these commands in VS Code terminal:
   ```bash
   git add README.md
   git commit -m "Add complete project README"
   git push origin main
