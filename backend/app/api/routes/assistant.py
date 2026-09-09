from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent
from app.schemas.schemas import ChatRequest
from app.services.assistant_handler import handle_conversation, SUGGESTIONS

router = APIRouter(tags=["assistant"])


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    db.add(AuditEvent(event_type="assistant_chat", payload=f"lang={payload.language}"))
    db.commit()
    return handle_conversation(payload.history, payload.language)