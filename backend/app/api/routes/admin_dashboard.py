from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import (
    AdminUser,
    ApplicationGuidance,
    AuditEvent,
    EligibilityCheck,
    Partner,
    Recommendation,
    Scheme,
)

router = APIRouter(tags=["admin-dashboard"])


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    total_schemes = db.query(Scheme).count()
    active_schemes = db.query(Scheme).filter(Scheme.active.is_(True)).count()
    total_partners = db.query(Partner).count()
    accepting_partners = db.query(Partner).filter(Partner.accepting_applications.is_(True)).count()
    limited_partners = db.query(Partner).filter(Partner.status == "limited").count()
    unavailable_partners = db.query(Partner).filter(Partner.status == "unavailable").count()
    total_applications = db.query(ApplicationGuidance).count()
    total_recommendations = db.query(Recommendation).count()
    total_checks = db.query(EligibilityCheck).count()
    total_events = db.query(AuditEvent).count()

    by_type = [
        {"name": t, "count": c}
        for t, c in db.query(Partner.type, func.count(Partner.id)).group_by(Partner.type).all()
    ]
    by_state = [
        {"state": s, "count": c}
        for s, c in db.query(Partner.state, func.count(Partner.id)).group_by(Partner.state).all()
    ]
    by_partner_status = [
        {"status": s, "count": c}
        for s, c in db.query(Partner.status, func.count(Partner.id)).group_by(Partner.status).all()
    ]
    by_application_state = [
        {"state": s, "count": c}
        for s, c in (
            db.query(Partner.state, func.count(ApplicationGuidance.id))
            .join(Partner, ApplicationGuidance.recommended_partner_id == Partner.id)
            .group_by(Partner.state)
            .all()
        )
    ]
    by_purpose = [
        {"purpose": s, "count": c}
        for s, c in db.query(Recommendation.scheme_id, func.count(Recommendation.id))
        .join(Scheme, Recommendation.scheme_id == Scheme.id)
        .group_by(Scheme.purpose)
        .all()
    ]
    by_purpose_fixed = []
    for row in db.query(Scheme.purpose, func.count(Recommendation.id)).join(
        Scheme, Recommendation.scheme_id == Scheme.id
    ).group_by(Scheme.purpose).all():
        by_purpose_fixed.append({"purpose": row[0], "count": row[1]})

    by_scheme = [
        {"scheme": s, "count": c}
        for s, c in db.query(Scheme.name, func.count(Recommendation.id))
        .join(Recommendation, Recommendation.scheme_id == Scheme.id)
        .group_by(Scheme.name)
        .order_by(func.count(Recommendation.id).desc())
        .all()
    ]

    return {
        "totals": {
            "schemes": total_schemes,
            "active_schemes": active_schemes,
            "partners": total_partners,
            "accepting_partners": accepting_partners,
            "limited_partners": limited_partners,
            "unavailable_partners": unavailable_partners,
            "applications": total_applications,
            "recommendations": total_recommendations,
            "eligibility_checks": total_checks,
            "events": total_events,
        },
        "by_type": by_type,
        "by_state": by_state,
        "by_partner_status": by_partner_status,
        "by_application_state": by_application_state,
        "by_purpose": by_purpose_fixed,
        "by_scheme": by_scheme,
        "demo_mode": True,
    }