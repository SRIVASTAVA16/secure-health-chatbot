# Secure AI-Driven Public Health Chatbot

A secure, explainable public health awareness chatbot that answers questions about diseases, symptoms, prevention, and healthy lifestyle using a verified knowledge base and a machine-learning pipeline. The system is designed for public health communication and **does not** provide medical diagnosis or treatment.

## 🔍 Key Features

- **Interactive chatbot UI (React)**  
  - Modern two-column layout with chat + system pipeline panel  
  - English / Hindi (Roman) language selector  
  - Persistent chat history (stored in browser) and recent question list  
  - Keyword highlighting to show important terms used in each answer  

- **Backend API (FastAPI)**  
  - `/api/chat` endpoint for health questions  
  - NLP preprocessing + **TF‑IDF** vectorization  
  - **Logistic Regression** classifier to detect topic/category  
  - Explainability: returns TF‑IDF keywords as “important factors”  

- **Verified Knowledge Base**  
  - Curated `health_knowledge.json` with WHO / official style content  
  - SHA‑256 hash computed for the KB file  
  - Ledger file + optional `EXPECTED_KB_HASH` env variable to detect tampering  
  - `/kb/hash` endpoint to expose hash + verification status  

- **Optional Gemini Integration**  
  - When local KB has low similarity, backend can call **Google Gemini**  
  - Gemini is instructed to answer **only health-related** queries  
  - Still appends safety disclaimer and keeps local explainability  

- **Safety & Scope Control**  
  - Heuristic filter: rejects non‑health queries (sports, politics, etc.)  
  - Strong disclaimer that it is **not a doctor** and not for emergencies  

## 🏗️ Tech Stack

- **Frontend**: React + TypeScript + Vite  
- **Backend**: FastAPI, Uvicorn  
- **ML / NLP**: scikit‑learn (TF‑IDF + LogisticRegression)  
- **Storage**: JSON knowledge base + hash ledger (no user data persistence)  

## 🚀 Running the Project Locally

### 1. Backend (FastAPI + ML engine)

From project root:

```bash
cd "C:\Users\ashmi\OneDrive - Lovely Professional University\CapstoneProjectApp"

# Install dependencies
pip install -r requirements.txt# Secure AI-Driven Public Health Chatbot

A secure, explainable public health awareness chatbot that answers questions about diseases, symptoms, prevention, and healthy lifestyle using a verified knowledge base and a machine-learning pipeline. The system is designed for public health communication and **does not** provide medical diagnosis or treatment.

## 🔍 Key Features

- **Interactive chatbot UI (React)**  
  - Modern two-column layout with chat + system pipeline panel  
  - English / Hindi (Roman) language selector  
  - Persistent chat history (stored in browser) and recent question list  
  - Keyword highlighting to show important terms used in each answer  

- **Backend API (FastAPI)**  
  - `/api/chat` endpoint for health questions  
  - NLP preprocessing + **TF‑IDF** vectorization  
  - **Logistic Regression** classifier to detect topic/category  
  - Explainability: returns TF‑IDF keywords as “important factors”  

- **Verified Knowledge Base**  
  - Curated `health_knowledge.json` with WHO / official style content  
  - SHA‑256 hash computed for the KB file  
  - Ledger file + optional `EXPECTED_KB_HASH` env variable to detect tampering  
  - `/kb/hash` endpoint to expose hash + verification status  

- **Optional Gemini Integration**  
  - When local KB has low similarity, backend can call **Google Gemini**  
  - Gemini is instructed to answer **only health-related** queries  
  - Still appends safety disclaimer and keeps local explainability  

- **Safety & Scope Control**  
  - Heuristic filter: rejects non‑health queries (sports, politics, etc.)  
  - Strong disclaimer that it is **not a doctor** and not for emergencies  

## 🏗️ Tech Stack

- **Frontend**: React + TypeScript + Vite  
- **Backend**: FastAPI, Uvicorn  
- **ML / NLP**: scikit‑learn (TF‑IDF + LogisticRegression)  
- **Storage**: JSON knowledge base + hash ledger (no user data persistence)  

## 🚀 Running the Project Locally

### 1. Backend (FastAPI + ML engine)

From project root:

```bash
cd "C:\Users\ashmi\OneDrive - Lovely Professional University\CapstoneProjectApp"

# Install dependencies
pip install -r requirements.txt

Test in browser:

API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health
KB hash status: http://localhost:8000/kb/hash

2. Frontend (React chatbot UI)
In another terminal:

cd "C:\Users\ashmi\OneDrive - Lovely Professional University\CapstoneProjectApp\frontend"
npm install
npm run dev
Open the URL shown by Vite, e.g.:

http://localhost:5173/ or http://localhost:5174/
🧠 System Pipeline
User question → frontend sends to /api/chat.
NLP & TF‑IDF → text normalized and vectorized.
ML classifier → predicts health topic/category.
Similarity search → finds most relevant KB article.
Security layer → KB hash/ledger verified at startup.
Explainable AI → top TF‑IDF keywords returned & highlighted.
Optional Gemini → used as fallback for health questions not covered by KB.
Response → chatbot UI shows answer, source link, and important factors.
⚠️ Disclaimer
This chatbot is for public health awareness and education only.
It does not provide medical diagnosis or treatment and must not be used for emergencies. For any serious or urgent symptoms, contact local emergency services or a qualified healthcare professional.
