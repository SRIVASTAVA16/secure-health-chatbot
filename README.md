# 🏥 Secure AI-Driven Public Health Chatbot

A secure, explainable public health awareness chatbot that answers questions about diseases, symptoms, prevention, and healthy lifestyle using a verified knowledge base and a machine-learning pipeline.

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
- **Language Support** — English / Hindi (Roman) selector
- **Session-based Chat** — Fresh chat on every new visit; continues on page refresh
- **Keyword Highlighting** — Important health terms highlighted in every answer
- **Health-only Guardrail** — Rejects non-health queries (sports, politics, etc.)
- **Explainable AI** — Returns top TF-IDF keywords as "important factors"
- **Verified Knowledge Base** — SHA-256 hash integrity check on the KB file
- **Safety Disclaimer** — Every response reminds users it is not a medical diagnosis tool

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Uvicorn |
| ML / NLP | scikit-learn (TF-IDF + Logistic Regression) |
| Storage | JSON knowledge base (no user data stored) |
| Deployment | Netlify (frontend) + Render (backend) |

---

## 🧠 System Pipeline

```
User question
    → NLP preprocessing (normalize, lowercase)
    → TF-IDF vectorization
    → Logistic Regression classifier (predict health topic)
    → Knowledge base lookup (find best matching article)
    → KB hash integrity check
    → Explainable AI (top TF-IDF keywords highlighted)
    → Response with answer, source, and important factors
```

---

## 🚀 Running Locally

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
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

---

## 📁 Project Structure

```
├── backend/
│   ├── app.py                  # FastAPI app + chat endpoint
│   ├── nlp_model.py            # TF-IDF + Logistic Regression pipeline
│   ├── security.py             # KB hash verification
│   ├── requirements.txt
│   └── data/
│       ├── health_knowledge.json   # Curated health KB
│       └── health_qa.csv           # Training data for classifier
├── frontend/
│   ├── src/
│   │   └── App.tsx             # React chatbot UI
│   └── index.html
├── netlify.toml                # Netlify deploy config
└── README.md
```

---

## ⚠️ Disclaimer

This chatbot is for **public health awareness and education only**. It does not provide medical diagnosis or treatment and must not be used for emergencies. For any serious or urgent symptoms, contact local emergency services or a qualified healthcare professional.
