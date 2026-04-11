# 🏥 Secure AI-Driven Public Health Chatbot

A secure, explainable public health awareness chatbot that answers questions about diseases, symptoms, prevention, and healthy lifestyle using a verified knowledge base, machine learning, and Google Gemini AI fallback.

> ⚠️ This system is designed for public health communication and **does not** provide medical diagnosis or treatment.

---

## 🔗 Live Demo

| Service | URL |
|--------|-----|
| 🌐 Frontend (Netlify) | [securehealthappp.netlify.app](https://securehealthappp.netlify.app) |
| ⚙️ Backend API (Render) | [secure-health-chatbot-1.onrender.com](https://secure-health-chatbot-1.onrender.com/docs) |
| 📦 GitHub Repo | [SRIVASTAVA16/secure-health-chatbot](https://github.com/SRIVASTAVA16/secure-health-chatbot) |

---

## ✨ Key Features

- **Interactive Chat UI** — React + TypeScript, two-column layout with chat and system pipeline panel
- **Voice Input** — Speak your health question using the built-in mic button (Web Speech API)
- **Language Support** — English / Hindi (Roman) selector
- **Session-based Chat** — Fresh chat on every new visit; continues on page refresh
- **Keyword Highlighting** — Important health terms highlighted in every answer
- **Intent Detection** — Detects personal symptom queries ("I have fever") and responds with general advice
- **Health-only Guardrail** — Rejects non-health queries (sports, politics, etc.)
- **Explainable AI** — Returns top TF-IDF keywords as "important factors"
- **Verified Knowledge Base** — SHA-256 hash integrity check on the KB file
- **Gemini AI Fallback** — Google Gemini API answers queries not covered by local KB
- **Confidence Score** — Each response shows prediction confidence
- **Safety Disclaimer** — Every response reminds users it is not a medical diagnosis tool

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite |
| Backend | FastAPI, Uvicorn |
| ML / NLP | scikit-learn (TF-IDF + Cosine Similarity) |
| AI Fallback | Google Gemini API (gemini-2.0-flash) |
| Knowledge Base | JSON (14,000+ medical Q&A entries from Kaggle) |
| Security | SHA-256 hash verification (response + KB integrity) |
| Deployment | Netlify (frontend) + Render (backend) |

---

## 🧠 System Pipeline

```
User question
    → Health domain guardrail (reject non-health queries)
    → Intent detection (personal symptom vs. disease query)
    → Direct KB title search (keyword matching)
    → TF-IDF + Cosine Similarity (semantic search)
    → KB hash integrity check (SHA-256)
    → Gemini AI fallback (if KB confidence is low)
    → Explainable AI (top TF-IDF keywords highlighted)
    → Response with answer, source, confidence score, and keywords
```

---

## 🚀 Running Locally

### 1. Backend

```bash
pip install -r requirements.txt
cd backend
python -m uvicorn main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

> Set `VITE_API_BASE=http://localhost:8000` in `frontend/.env` to use local backend.

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py               # FastAPI app + endpoints
│   └── pipeline.py           # ML pipeline, KB search, Gemini fallback
├── data/
│   ├── health_knowledge.json # 14,000+ medical Q&A knowledge base
│   └── health_knowledge.ledger # SHA-256 integrity ledger
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # React chatbot UI
│   │   └── style.css         # Styles
│   └── index.html
├── requirements.txt          # Python dependencies
├── netlify.toml              # Netlify deploy config
└── README.md
```

---

## 🔐 Security Features

- **KB Integrity Verification** — SHA-256 hash of the knowledge base is stored in a ledger file. On every startup, the hash is recomputed and compared. If tampered, the server refuses to start.
- **Response Hashing** — Every response is hashed with SHA-256 for auditability.
- **Health Domain Guardrail** — Strict filtering ensures only health-related queries are answered.

---

## ⚠️ Disclaimer

This chatbot is for **public health awareness and education only**. It does not provide medical diagnosis or treatment and must not be used for emergencies. For any serious or urgent symptoms, contact local emergency services or a qualified healthcare professional.
