from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "health_knowledge.json")
LEDGER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "health_knowledge.ledger")

# General symptom advice for personal symptom queries
SYMPTOM_ADVICE: Dict[str, str] = {
    "fever": "Fever is a rise in body temperature, usually a sign your body is fighting an infection. Rest, drink plenty of fluids, and take paracetamol if needed. See a doctor if fever exceeds 103°F (39.4°C), lasts more than 3 days, or is accompanied by severe symptoms.",
    "headache": "Headaches can be caused by dehydration, stress, lack of sleep, or illness. Rest, drink water, and take a mild painkiller if needed. Seek medical help if the headache is sudden and severe or accompanied by fever and stiff neck.",
    "cough": "A cough is often caused by a cold, flu, or throat irritation. Stay hydrated and avoid irritants. See a doctor if the cough lasts more than 2 weeks, produces blood, or is accompanied by breathing difficulty.",
    "cold": "The common cold is a viral infection. Rest, drink fluids, and use saline nasal drops. Symptoms usually resolve in 7-10 days.",
    "vomiting": "Stay hydrated with small sips of water or oral rehydration solution. Avoid solid food until vomiting stops. Seek medical help if it persists more than 24 hours.",
    "diarrhea": "Drink oral rehydration solution to prevent dehydration. Avoid dairy and fatty foods. See a doctor if it lasts more than 2 days or contains blood.",
    "stomach pain": "Rest and avoid heavy meals. Seek immediate medical help if pain is severe, sudden, or accompanied by fever.",
    "chest pain": "Chest pain can be serious. Seek emergency medical help immediately if you experience chest pain with shortness of breath or sweating.",
    "rash": "Avoid scratching and apply a cool compress. See a doctor if the rash spreads, blisters, or is accompanied by fever.",
    "fatigue": "Rest, eat a balanced diet, and stay hydrated. See a doctor if fatigue is persistent and unexplained.",
    "sore throat": "Gargle with warm salt water, stay hydrated, and rest. See a doctor if it is severe or lasts more than a week.",
    "nausea": "Eat small bland meals, stay hydrated, and rest. See a doctor if it persists or is accompanied by severe vomiting.",
    "body pain": "Rest, stay hydrated, and take paracetamol for relief. See a doctor if pain is severe or persistent.",
    "breathing": "Difficulty breathing can be a medical emergency. Call emergency services immediately if severe.",
}

NON_HEALTH_TERMS = [
    "cricket", "ipl", "football", "movie", "film", "song", "music", "politics",
    "election", "president", "prime minister", "capital", "country", "stock",
    "market", "exam", "study", "school", "college", "university", "math",
    "science", "history", "geography", "weather", "rain", "temperature outside",
]

HEALTH_TERMS = [
    "health", "disease", "fever", "cough", "infection", "virus", "bacteria",
    "covid", "corona", "diabetes", "sugar", "hypertension", "blood pressure",
    "cholesterol", "symptom", "prevention", "vaccine", "vaccination", "doctor",
    "hospital", "treatment", "medicine", "medication", "pain", "rash", "dengue",
    "malaria", "typhoid", "asthma", "cancer", "heart", "kidney", "liver", "lung",
    "headache", "vomit", "diarrhea", "nausea", "fatigue", "cold", "flu", "throat",
    "chest", "breathing", "skin", "allergy", "injury", "wound", "bleeding",
    "tuberculosis", "tb", "pneumonia", "cholera", "hepatitis", "hiv", "aids",
    "chickenpox", "measles", "jaundice", "stroke", "epilepsy", "migraine",
    "i have", "i am having", "i feel", "suffering", "hurts", "sick", "ill",
]


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
                raise ValueError("Health knowledge base failed integrity verification.")

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
        self.gemini_api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
        self._load_and_prepare()

    def _load_and_prepare(self) -> None:
        self.verifier.verify_or_initialize()
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self.knowledge_items = [
            KnowledgeItem(id=i, title=item["title"], text=item["text"][:600],
                          category=item["category"], url=item.get("url", ""))
            for i, item in enumerate(raw[:1500])
        ]

        documents = [f"{item.title} {item.text}" for item in self.knowledge_items]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=2000)
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

    def _is_health_query(self, message: str) -> bool:
        msg = message.lower()
        if any(t in msg for t in NON_HEALTH_TERMS):
            # Only reject if NO health terms present
            if not any(t in msg for t in HEALTH_TERMS):
                return False
        return any(t in msg for t in HEALTH_TERMS) or len(msg.split()) <= 3

    def _is_personal_symptom(self, message: str) -> bool:
        msg = message.lower()
        patterns = [r"\bi (have|am having|feel|got|am feeling)\b", r"\bmy (head|stomach|chest|body|throat)\b",
                    r"\bhurts?\b", r"\bsuffering\b", r"\bsick\b", r"\bill\b"]
        return any(re.search(p, msg) for p in patterns)

    def _get_symptom_advice(self, message: str) -> Optional[str]:
        msg = message.lower()
        for keyword, advice in SYMPTOM_ADVICE.items():
            if keyword in msg:
                return advice
        return None

    def _kb_search(self, query: str) -> tuple[KnowledgeItem, float]:
        assert self.vectorizer is not None and self.tfidf_matrix is not None
        qvec = self.vectorizer.transform([query])
        scores = cosine_similarity(qvec, self.tfidf_matrix).ravel()
        idx = int(np.argmax(scores))
        return self.knowledge_items[idx], float(scores[idx])

    def _title_matches_query(self, query: str, title: str) -> bool:
        stop = {"what", "is", "are", "the", "how", "to", "of", "a", "an", "i",
                "have", "my", "do", "does", "can", "be", "symptoms", "symptom",
                "about", "tell", "me", "explain"}
        qwords = set(re.sub(r'[^\w\s]', '', query.lower()).split()) - stop
        twords = set(title.lower().split())
        return bool(qwords & twords)

    def _extract_keywords(self, query: str, top_k: int = 5) -> List[str]:
        assert self.vectorizer is not None
        qvec = self.vectorizer.transform([query]).toarray().ravel()
        features = np.array(self.vectorizer.get_feature_names_out())
        if qvec.sum() == 0:
            return []
        top = np.argsort(qvec)[-top_k:][::-1]
        return [features[i] for i in top if qvec[i] > 0]

    def _call_gemini(self, message: str) -> Optional[str]:
        if not self.gemini_api_key:
            return None
        try:
            payload = {
                "systemInstruction": {"parts": [{"text": (
                    "You are a public health awareness assistant. Answer ONLY health questions. "
                    "Give SHORT answers in 4-6 lines. Do not assume rare diseases. "
                    "Always advise consulting a doctor."
                )}]},
                "contents": [{"parts": [{"text": message}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300},
            }
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers={"x-goog-api-key": self.gemini_api_key, "Content-Type": "application/json"},
                json=payload, timeout=15
            )
            resp.raise_for_status()
            candidates = resp.json().get("candidates") or []
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts") or []
            return "\n".join(p.get("text", "") for p in parts if p.get("text", "").strip()) or None
        except Exception as e:
            print(f"[Gemini error] {e}")
            return None

    def answer_question(self, message: str, language: str = "en") -> Dict[str, Any]:
        processed = message.strip().lower()
        keywords = self._extract_keywords(processed)

        # Out-of-domain check
        if not self._is_health_query(processed):
            answer = ("I am designed strictly for public health awareness. "
                      "I can answer questions about diseases, symptoms, prevention, "
                      "vaccination, and healthy lifestyle.")
            return {
                "answer": answer, "source_title": "Health domain only",
                "source_url": None, "important_keywords": [],
                "detected_category": "out-of-domain", "language": language,
                "confidence": 0, "response_hash": sha256(answer.encode()).hexdigest(),
                "kb_verified": self.verifier.valid,
            }

        answer_text: Optional[str] = None
        source_title = "General Health Guidelines"
        source_url: Optional[str] = None

        # Step 1: Personal symptom query ("I have fever")
        if self._is_personal_symptom(processed):
            answer_text = self._get_symptom_advice(processed)
            if answer_text:
                source_title = "General Symptom Advice"

        # Step 2: Direct title search — disease name must match, not just generic words
        if not answer_text:
            query_words = set(re.sub(r'[^\w\s]', '', processed).split())
            stop = {"what", "is", "are", "the", "how", "to", "of", "a", "an", "i",
                    "have", "my", "do", "does", "can", "be", "about", "tell", "me",
                    "symptoms", "symptom", "disease", "treatment", "prevent", "prevention",
                    "causes", "cause", "cure", "information", "info", "explain", "definition"}
            meaningful_words = query_words - stop
            if meaningful_words:
                best_item = None
                best_overlap = 0
                for ki in self.knowledge_items:
                    title_words = set(ki.title.lower().split())
                    # Remove stop words from title too for fair comparison
                    title_meaningful = title_words - stop
                    overlap = len(meaningful_words & title_meaningful)
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_item = ki
                if best_item and best_overlap >= 1:
                    answer_text = best_item.text
                    source_title = best_item.title
                    source_url = best_item.url or None
                    confidence = 80

        # Step 3: Cosine similarity KB search
        if not answer_text:
            item, score = self._kb_search(processed)
            confidence = round(score * 100, 1)
            if score >= 0.10 and self._title_matches_query(processed, item.title):
                answer_text = item.text
                source_title = item.title
                source_url = item.url or None

        # Step 3: Gemini fallback
        if not answer_text:
            print(f"[Gemini fallback] query={processed[:60]}")
            answer_text = self._call_gemini(message)
            if answer_text:
                source_title = "Gemini health assistant"
            else:
                answer_text = ("I couldn't find a specific answer. "
                               "Please consult a qualified healthcare professional.")

        answer_text = (f"{answer_text}\n\n"
                       f"⚠️ This is for general awareness only. "
                       f"Please consult a qualified doctor for personal advice.")

        return {
            "answer": answer_text,
            "source_title": source_title,
            "source_url": source_url,
            "important_keywords": keywords,
            "detected_category": "Health",
            "language": language,
            "confidence": confidence if 'confidence' in dir() else 50,
            "response_hash": sha256(answer_text.encode()).hexdigest(),
            "kb_verified": self.verifier.valid,
        }
