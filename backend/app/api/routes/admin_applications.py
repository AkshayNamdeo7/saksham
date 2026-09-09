from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser, ApplicationGuidance, Recommendation

router = APIRouter(tags=["admin-applications"])


@router.get("/applications")
def list_app_guidance(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    rows = (
        db.query(ApplicationGuidance)
        .order_by(ApplicationGuidance.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": g.id,
            "scheme_name": g.scheme.name if g.scheme else None,
            "partner_name": g.recommended_partner.name if g.recommended_partner else None,
            "partner_score": g.partner_score,
            "loan_required": g.loan_required,
            "guidance_summary": g.guidance_summary,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in rows
    ]


@router.get("/recommendations")
def list_recommendations(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    rows = db.query(Recommendation).order_by(Recommendation.created_at.desc()).limit(200).all()
    return [
        {
            "id": r.id,
            "scheme_name": r.scheme.name if r.scheme else None,
            "match_score": r.match_score,
            "eligibility_status": r.eligibility_status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]