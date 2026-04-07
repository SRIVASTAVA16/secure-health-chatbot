from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
import numpy as np
import requests

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "health_knowledge.json",
)
LEDGER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "health_knowledge.ledger",
)

# General symptom advice — handles "I have fever", "headache", etc.
GENERAL_SYMPTOM_ADVICE: Dict[str, str] = {
    "fever": "Fever is a temporary rise in body temperature, often a sign your body is fighting an infection. Rest, drink plenty of fluids, and take paracetamol if needed. See a doctor if fever exceeds 103°F (39.4°C), lasts more than 3 days, or is accompanied by severe symptoms.",
    "headache": "Headaches can be caused by dehydration, stress, lack of sleep, or illness. Rest in a quiet dark room, drink water, and take a mild painkiller if needed. Seek medical help if the headache is sudden and severe or accompanied by fever and stiff neck.",
    "cough": "A cough is often caused by a cold, flu, or throat irritation. Stay hydrated, use honey and warm water, and avoid irritants. See a doctor if the cough lasts more than 2 weeks, produces blood, or is accompanied by breathing difficulty.",
    "cold": "The common cold is a viral infection. Rest, drink fluids, and use saline nasal drops. Symptoms usually resolve in 7–10 days. See a doctor if symptoms worsen or you develop high fever.",
    "vomiting": "Vomiting can be caused by food poisoning, viral infection, or other conditions. Stay hydrated with small sips of water or oral rehydration solution. Avoid solid food until vomiting stops. Seek medical help if it persists more than 24 hours.",
    "diarrhea": "Diarrhea is often caused by infection or food poisoning. Drink oral rehydration solution to prevent dehydration. Avoid dairy and fatty foods. See a doctor if it lasts more than 2 days or contains blood.",
    "stomach pain": "Stomach pain can have many causes including indigestion, gas, or infection. Rest and avoid heavy meals. Seek immediate medical help if pain is severe, sudden, or accompanied by fever.",
    "chest pain": "Chest pain can be a sign of a serious condition. Seek emergency medical help immediately if you experience chest pain, especially with shortness of breath, sweating, or pain radiating to the arm.",
    "breathing": "Difficulty breathing can be a medical emergency. If you are experiencing severe shortness of breath, call emergency services immediately.",
    "rash": "Skin rashes can be caused by allergies, infections, or other conditions. Avoid scratching and apply a cool compress. See a doctor if the rash spreads, blisters, or is accompanied by fever.",
    "fatigue": "Fatigue or tiredness can result from lack of sleep, poor nutrition, stress, or illness. Rest, eat a balanced diet, and stay hydrated. See a doctor if fatigue is persistent and unexplained.",
    "sore throat": "A sore throat is usually caused by a viral infection. Gargle with warm salt water, stay hydrated, and rest. See a doctor if it is severe, lasts more than a week, or is accompanied by high fever.",
    "body pain": "Body aches are common with flu and viral infections. Rest, stay hydrated, and take paracetamol for relief. See a doctor if pain is severe or persistent.",
    "nausea": "Nausea can be caused by infections, food poisoning, or other conditions. Eat small bland meals, stay hydrated, and rest. See a doctor if it persists or is accompanied by severe vomiting.",
}


@dataclass
class KnowledgeItem:
    id: int
    title: str
    text: str
    category: str
    url: str


class KnowledgeVerifier:
    def __init__(self, data_path: str = DATA_PATH, ledger_path: str = LEDGER_PATH):
        self.data_path = data_path
        self.ledger_path = ledger_path
        self.expected_hash: str | None = os.environ.get("EXPECTED_KB_HASH")
        self.current_hash: str | None = None
        self.ledger_hash: str | None = None
        self.valid: bool = False

    def _compute_hash(self, content: bytes) -> str:
        return sha256(content).hexdigest()

    def verify_or_initialize(self) -> None:
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        content = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.current_hash = self._compute_hash(content)

        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                f.write(self.current_hash)
            self.ledger_hash = self.current_hash
        else:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                self.ledger_hash = f.read().strip()
            if self.ledger_hash != self.current_hash:
                raise ValueError(
                    "Health knowledge base failed integrity verification. "
                    "Ledger hash does not match current data hash; data may have been modified."
                )

        if self.expected_hash and self.expected_hash != self.current_hash:
            raise ValueError("Health knowledge base failed EXPECTED_KB_HASH verification.")

        self.valid = True

    def status(self) -> Dict[str, Any]:
        return {
            "current_hash": self.current_hash,
            "ledger_hash": self.ledger_hash,
            "expected_hash": self.expected_hash,
            "valid": self.valid,
        }


class HealthChatbotEngine:
    def __init__(self) -> None:
        self.verifier = KnowledgeVerifier()
        self.knowledge_items: List[KnowledgeItem] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.tfidf_matrix = None
        self.label_encoder: LabelEncoder | None = None
        self.kb_status: Dict[str, Any] | None = None
        self.gemini_api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
        self._load_and_prepare()

    def _load_and_prepare(self) -> None:
        self.verifier.verify_or_initialize()
        self.kb_status = self.verifier.status()

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self.knowledge_items = [
            KnowledgeItem(
                id=i,
                title=item["title"],
                text=item["text"][:600],  # truncate long texts
                category=item["category"],
                url=item.get("url", ""),
            )
            for i, item in enumerate(raw[:1500])
        ]

        documents = [f"{item.title}. {item.text}" for item in self.knowledge_items]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=2000,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

    def _preprocess(self, text: str) -> str:
        return text.strip().lower()

    def _detect_intent(self, message: str) -> Optional[str]:
        """Rule-based intent detection before ML."""
        msg = message.lower()
        symptom_patterns = [
            r"\bi (have|am having|feel|got|am feeling)\b",
            r"\bmy (head|stomach|chest|body|throat|eye|ear|back|leg|arm)\b",
            r"\bi (can't|cannot) (breathe|sleep|eat)\b",
            r"\bhurts?\b", r"\bpain\b", r"\baching\b", r"\bsuffering\b",
        ]
        for pattern in symptom_patterns:
            if re.search(pattern, msg):
                return "symptom_advice"
        return None

    def _check_general_symptoms(self, message: str) -> Optional[str]:
        """Check if message matches a general symptom we have advice for."""
        msg = message.lower()
        for keyword, advice in GENERAL_SYMPTOM_ADVICE.items():
            if keyword in msg:
                return advice
        return None

    def _cosine_search(self, query: str) -> tuple[KnowledgeItem, float]:
        """Find best KB match using cosine similarity."""
        assert self.vectorizer is not None and self.tfidf_matrix is not None
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).ravel()
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])
        return self.knowledge_items[best_idx], best_score

    def _extract_keywords(self, query: str, top_k: int = 5) -> List[str]:
        assert self.vectorizer is not None
        query_vec = self.vectorizer.transform([query]).toarray().ravel()
        feature_names = np.array(self.vectorizer.get_feature_names_out())
        if query_vec.sum() == 0:
            return []
        top_indices = np.argsort(query_vec)[-top_k:][::-1]
        return [feature_names[i] for i in top_indices if query_vec[i] > 0]

    def _is_health_query(self, message: str, score: float) -> bool:
        text = message.lower()
        health_terms = [
            "health", "disease", "fever", "bukhar", "cough", "khansi",
            "infection", "virus", "bacteria", "covid", "corona", "sardi",
            "diabetes", "sugar", "hypertension", "blood pressure", "bp",
            "cholesterol", "symptom", "lakshan", "prevention", "vaccine",
            "vaccination", "doctor", "hospital", "clinic", "treatment",
            "ilaaj", "medicine", "dawai", "medication", "pain", "dard",
            "rash", "mosquito", "dengue", "malaria", "typhoid", "asthma",
            "cancer", "heart", "kidney", "liver", "lung", "headache",
            "vomit", "diarrhea", "nausea", "fatigue", "tired", "weak",
            "injury", "wound", "bleeding", "allergy", "cold", "flu",
            "throat", "chest", "breathing", "eye", "vision", "skin",
            "i have", "i am having", "i feel", "suffering", "hurts",
        ]
        if any(term in text for term in health_terms):
            return True
        if score >= 0.05:
            return True
        return False

    def _call_gemini(self, message: str, language: str) -> Optional[str]:
        if not self.gemini_api_key:
            print("[Gemini] No API key set")
            return None

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-2.0-flash:generateContent"
        )
        system_prompt = (
            "You are a public health awareness assistant. "
            "Answer ONLY health-related questions about diseases, symptoms, prevention, "
            "vaccines, and healthy lifestyle. "
            "Give SHORT, SIMPLE answers in 4-6 lines. "
            "Do NOT assume rare diseases. Focus on common explanations. "
            "Do NOT give long medical articles or prescribe medicines. "
            "Always remind the user to consult a doctor for personal advice."
        )

        try:
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": message}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300},
            }
            headers = {
                "x-goog-api-key": self.gemini_api_key,
                "Content-Type": "application/json",
            }
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts") or []
            texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
            combined = "\n".join(t for t in texts if t.strip())
            return combined or None
        except Exception as e:
            print(f"[Gemini error] {e}")
            return None

    def answer_question(self, message: str, language: str = "en") -> Dict[str, Any]:
        processed = self._preprocess(message)
        keywords = self._extract_keywords(processed)
        item, score = self._cosine_search(processed)

        if not self._is_health_query(processed, score):
            answer_text = (
                "I am designed strictly for public health awareness. "
                "I can answer questions about diseases, symptoms, prevention, "
                "vaccination, and healthy lifestyle. I cannot answer questions "
                "about sports, politics, exams, or other non-health topics."
            )
            return {
                "answer": answer_text,
                "source_title": "Health domain only",
                "source_url": None,
                "important_keywords": [],
                "detected_category": "out-of-domain",
                "language": language,
                "confidence": 0,
                "response_hash": sha256(answer_text.encode()).hexdigest(),
                "kb_verified": self.verifier.valid,
            }

        answer_text: Optional[str] = None
        source_title = "General Health Guidelines"
        source_url: Optional[str] = None
        confidence = round(score * 100, 1)

        # 1. Intent detection — handle "I have fever" type queries first
        intent = self._detect_intent(processed)
        if intent == "symptom_advice":
            general = self._check_general_symptoms(processed)
            if general:
                answer_text = general
                source_title = "General Symptom Advice"

        # 2. High-confidence KB match
        if not answer_text and score >= 0.20:
            answer_text = item.text[:500]
            source_title = item.title
            source_url = item.url or None

        # 3. Gemini fallback
        if not answer_text:
            print(f"[Gemini] score={score:.3f} query={processed[:60]}")
            gemini_answer = self._call_gemini(message, language)
            if gemini_answer:
                answer_text = gemini_answer
                source_title = "Gemini health assistant"
            else:
                answer_text = (
                    "I couldn't find a specific answer for your query. "
                    "Please consult a qualified healthcare professional for personalised advice."
                )

        answer_text = (
            f"{answer_text}\n\n"
            f"⚠️ This is for general awareness only. Please consult a qualified doctor "
            f"for personal diagnosis or treatment."
        )

        return {
            "answer": answer_text,
            "source_title": source_title,
            "source_url": source_url,
            "important_keywords": keywords,
            "detected_category": item.category,
            "language": language,
            "confidence": confidence,
            "response_hash": sha256(answer_text.encode()).hexdigest(),
            "kb_verified": self.verifier.valid,
        }
