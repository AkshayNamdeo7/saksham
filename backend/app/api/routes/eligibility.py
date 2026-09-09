from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent, EligibilityCheck
from app.schemas.schemas import EligibilityCheckRequest

router = APIRouter(tags=["eligibility"])


@router.post("/check")
def check_eligibility(payload: EligibilityCheckRequest, db: Session = Depends(get_db)):
    rec = EligibilityCheck(
        age=payload.age,
        state=payload.state,
        district=payload.district,
        city=payload.city,
        annual_family_income=payload.annual_family_income,
        purpose=payload.purpose,
        project_type=payload.project_type,
        project_cost=payload.project_cost,
        education_level=payload.education_level,
        course_type=payload.course_type,
        requested_loan=payload.requested_loan,
    )
    db.add(rec)
    db.flush()
    db.add(AuditEvent(event_type="eligibility_check", payload=f"id={rec.id} purpose={payload.purpose}"))
    db.commit()
    return {"check_id": rec.id, "accepted": True, "profile": payload.model_dump()}