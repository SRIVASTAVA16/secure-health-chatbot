from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from .pipeline import HealthChatbotEngine


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    answer: str
    source_title: str
    source_url: Optional[str] = None
    important_keywords: List[str]
    detected_category: Optional[str] = None
    language: str


class KnowledgeStatusResponse(BaseModel):
    current_hash: Optional[str] = None
    ledger_hash: Optional[str] = None
    expected_hash: Optional[str] = None
    valid: bool


app = FastAPI(title="Secure AI-Driven Public Health Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = HealthChatbotEngine()


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "kb_status": engine.verifier.status(),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = engine.answer_question(request.message, request.language or "en")
    return ChatResponse(**result)


@app.get("/kb/hash", response_model=KnowledgeStatusResponse)
def knowledge_hash() -> KnowledgeStatusResponse:
    """
    Helper endpoint to expose the current knowledge base hash information.
    The frontend can use this to show a simple 'verified/compromised' badge.
    """
    status = engine.verifier.status()
    return KnowledgeStatusResponse(**status)

