from __future__ import annotations

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
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
        # Optional expected hash from environment for extra security
        self.expected_hash: str | None = os.environ.get("EXPECTED_KB_HASH")
        self.current_hash: str | None = None
        self.ledger_hash: str | None = None
        self.valid: bool = False

    def _compute_hash(self, content: bytes) -> str:
        return sha256(content).hexdigest()

    def verify_or_initialize(self) -> None:
        # Normalize by parsing and re-serializing to avoid CRLF/LF differences
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        content = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.current_hash = self._compute_hash(content)

        # Initialize ledger on first run
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
                    "Ledger hash does not match current data hash; data may "
                    "have been modified."
                )

        # Optional environment-based expected hash check
        if self.expected_hash and self.expected_hash != self.current_hash:
            raise ValueError(
                "Health knowledge base failed EXPECTED_KB_HASH verification. "
                "Environment hash does not match current data hash."
            )

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
        self.tfidf_matrix: np.ndarray | None = None
        self.classifier: Pipeline | None = None
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
                text=item["text"],
                category=item["category"],
                url=item.get("url", ""),
            )
            for i, item in enumerate(raw[:3000])  # cap at 3000 to stay within 512MB
        ]

        documents = [f"{item.title}. {item.text}" for item in self.knowledge_items]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=2000,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

        self.label_encoder = LabelEncoder()
        labels = self.label_encoder.fit_transform(
            [item.category for item in self.knowledge_items]
        )

        self.classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
                ("clf", LogisticRegression(max_iter=1000)),
            ]
        )
        self.classifier.fit(documents, labels)

    def _preprocess(self, text: str) -> str:
        return text.strip()

    def _most_relevant_item(
        self, query: str
    ) -> tuple[KnowledgeItem, np.ndarray, float]:
        assert self.vectorizer is not None and self.tfidf_matrix is not None
        query_vec = self.vectorizer.transform([query])
        scores = (self.tfidf_matrix @ query_vec.T).toarray().ravel()
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])
        return self.knowledge_items[best_idx], query_vec.toarray().ravel(), best_score

    def _classify_category(self, query: str) -> str:
        assert self.classifier is not None and self.label_encoder is not None
        probs = self.classifier.predict_proba([query])[0]
        best_label = int(np.argmax(probs))
        return str(self.label_encoder.inverse_transform([best_label])[0])

    def _extract_keywords(self, query_vec: np.ndarray, top_k: int = 5) -> List[str]:
        assert self.vectorizer is not None
        feature_names = np.array(self.vectorizer.get_feature_names_out())
        if query_vec.sum() == 0:
            return []
        top_indices = np.argsort(query_vec)[-top_k:][::-1]
        return [feature_names[i] for i in top_indices if query_vec[i] > 0]

    def _is_health_query(
        self, message: str, similarity_score: float, keywords: List[str]
    ) -> bool:
        """
        Heuristic filter to keep the chatbot strictly in the health domain.
        If similarity to any health document is very low AND the text does not
        contain common health-related terms, we treat it as out-of-domain.
        """
        text = message.lower()
        # Include both English and common Roman Hindi health words
        health_terms = [
            "health",
            "disease",
            "fever",
            "bukhar",
            "cough",
            "khansi",
            "infection",
            "virus",
            "bacteria",
            "covid",
            "corona",
            "sardi",
            "diabetes",
            "sugar",
            "hypertension",
            "blood pressure",
            "bp",
            "cholesterol",
            "symptom",
            "lakshan",
            "prevention",
            "vaccine",
            "vaccination",
            "doctor",
            "doctor sahab",
            "hospital",
            "clinic",
            "treatment",
            "ilaaj",
            "medicine",
            "dawai",
            "medication",
            "pain",
            "dard",
            "rash",
            "mosquito",
            "dengue",
            "eye",
            "eyesight",
            "vision",
        ]

        # If clear health terms are present, accept even with low similarity.
        if any(term in text for term in health_terms):
            return True

        # If TF-IDF similarity is reasonably high, we also accept it.
        # Lower threshold a bit so genuine but short health queries are not rejected.
        if similarity_score >= 0.03:
            return True

        # If extracted keywords look medical, allow.
        if any(term in " ".join(keywords).lower() for term in health_terms):
            return True

        return False

    def _call_gemini(self, message: str, language: str) -> Optional[str]:
        """
        Optional fallback to Gemini API for broader health answers when the
        local knowledge base has low coverage.
        """
        if not self.gemini_api_key:
            return None

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-2.0-flash:generateContent"
        )
        system_prompt = (
            "You are a public health awareness assistant. "
            "Answer ONLY questions related to health, diseases, symptoms, "
            "prevention, vaccines, and healthy lifestyle. "
            "Base your information on reputable organizations such as WHO "
            "and national health authorities. Keep answers short (4-8 lines), "
            "clear, and easy to understand. Never give definitive diagnoses "
            "or prescribe specific medicines. Always remind the user that this "
            "is not a replacement for a doctor."
        )

        try:
            payload = {
                "systemInstruction": {
                    "parts": [{"text": system_prompt}],
                },
                "contents": [
                    {
                        "parts": [
                            {"text": message},
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 512,
                },
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
        item, query_vec, score = self._most_relevant_item(processed)
        category = self._classify_category(processed)
        keywords = self._extract_keywords(query_vec)

        # Confidence score from classifier
        assert self.classifier is not None and self.label_encoder is not None
        probs = self.classifier.predict_proba([processed])[0]
        confidence = round(float(np.max(probs)) * 100, 1)

        if not self._is_health_query(processed, score, keywords):
            answer_text = (
                "I am designed strictly for public health awareness. "
                "I can answer questions about diseases, symptoms, prevention, "
                "vaccination, and healthy lifestyle. I cannot answer questions "
                "about sports, politics, exams, or other non‑health topics."
            )
            response_hash = sha256(answer_text.encode()).hexdigest()
            return {
                "answer": answer_text,
                "source_title": "Health domain only",
                "source_url": None,
                "important_keywords": [],
                "detected_category": "out-of-domain",
                "language": language,
                "confidence": 0,
                "response_hash": response_hash,
                "kb_verified": self.verifier.valid,
            }

        answer_text: Optional[str] = None
        source_title: str = item.title
        source_url: Optional[str] = item.url

        if score >= 0.05:
            answer_text = item.text
        else:
            gemini_answer = self._call_gemini(processed, language)
            if gemini_answer:
                answer_text = gemini_answer
                source_title = "Gemini health assistant"
                source_url = None
            else:
                answer_text = (
                    "I am a public health awareness bot. Your query is too broad "
                    "or not in my database. Could you please be more specific? "
                    "For example, are you asking about symptoms of a specific disease?"
                )
                source_title = "General Health Guidelines"
                source_url = None

        answer_text = (
            f"{answer_text}\n\n"
            f"This information is for general awareness only and does not replace "
            f"professional medical advice. Please consult a qualified doctor for "
            f"personal diagnosis or treatment."
        )

        response_hash = sha256(answer_text.encode()).hexdigest()

        return {
            "answer": answer_text,
            "source_title": source_title,
            "source_url": source_url,
            "important_keywords": keywords,
            "detected_category": category,
            "language": language,
            "confidence": confidence,
            "response_hash": response_hash,
            "kb_verified": self.verifier.valid,
        }

