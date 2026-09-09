from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent, ApplicationGuidance, Scheme
from app.schemas.schemas import PartnerRecommendRequest
from app.services.partner_routing import route_partners

router = APIRouter(tags=["partners"])


@router.post("/recommend")
def recommend_partners(payload: PartnerRecommendRequest, db: Session = Depends(get_db)):
    profile = {
        "state": payload.state,
        "district": payload.district,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "scheme_id": payload.scheme_id,
        "purpose": payload.purpose,
        "loan_amount": payload.loan_amount,
    }
    scored = route_partners(profile, db)[: payload.limit]

    db.add(AuditEvent(event_type="partner_recommend", payload=f"scheme={payload.scheme_id}"))
    db.commit()

    return {
        "weights": {"eligibility": 40, "scheme": 30, "distance": 20, "capacity": 10},
        "results": [
            {
                "partner": sp["partner"].id if hasattr(sp["partner"], "id") else sp["partner"].id,
                "partner_name": sp["partner"].name,
                "partner_type": sp["partner"].type,
                "state": sp["partner"].state,
                "district": sp["partner"].district,
                "city": sp["partner"].city,
                "address": sp["partner"].address,
                "latitude": sp["partner"].latitude,
                "longitude": sp["partner"].longitude,
                "status": sp["partner"].status,
                "capacity_pct": sp["partner"].capacity_pct,
                "fund_utilization_pct": sp["partner"].fund_utilization_pct,
                "npa_indicator": sp["partner"].npa_indicator,
                "phone": sp["partner"].phone,
                "email": sp["partner"].email,
                "accepting_applications": sp["partner"].accepting_applications,
                "is_demo": sp["partner"].is_demo,
                "supported_schemes": [
                    {"id": s.id, "name": s.name} for s in sp["partner"].schemes
                ],
                "breakdown": sp["points"],
                "total_score": sp["total"],
                "distance_km": sp["distance_km"],
                "notes": sp["notes"],
            }
            for sp in scored
        ],
    }


@router.post("/application-route")
def application_route(payload: PartnerRecommendRequest, db: Session = Depends(get_db)):
    """Persist application guidance with recommended partner."""
    scored = route_partners(
        {
            "state": payload.state,
            "district": payload.district,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "scheme_id": payload.scheme_id,
            "purpose": payload.purpose,
            "loan_amount": payload.loan_amount,
        },
        db,
    )
    if not scored:
        return {"guides": []}
    top = scored[0]
    scheme = db.query(Scheme).filter(Scheme.id == payload.scheme_id).first() if payload.scheme_id else None
    guidance = ApplicationGuidance(
        scheme_id=payload.scheme_id,
        recommended_partner_id=top["partner"].id,
        loan_required=payload.loan_amount,
        partner_score=top["total"],
        guidance_summary=(
            f"{scheme.name} via {top['partner'].name} (demo routing score "
            f"{top['total']}/100)" if scheme else f"via {top['partner'].name}"
        ),
    )
    db.add(guidance)
    db.add(AuditEvent(event_type="application_guidance", payload=f"guidance={guidance.id}"))
    db.commit()
    return {"guide_id": guidance.id, "partner_score": top["total"]}