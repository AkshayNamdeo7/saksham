import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent, EligibilityCheck, Recommendation, Scheme
from app.schemas.schemas import RecommendRequest
from app.services.ai_service import ai_service
from app.services.recommendation_engine import recommend

router = APIRouter(tags=["recommendations"])


@router.post("")
def get_recommendations(payload: RecommendRequest, db: Session = Depends(get_db)):
    profile = payload.profile.model_dump()
    results = recommend(profile, db, payload.scheme_ids)

    # persist eligibility check + top recommendation
    check = EligibilityCheck(
        age=profile.get("age"),
        state=profile.get("state"),
        district=profile.get("district"),
        city=profile.get("city"),
        annual_family_income=profile.get("annual_family_income"),
        purpose=profile.get("purpose"),
        project_type=profile.get("project_type"),
        project_cost=profile.get("project_cost"),
        education_level=profile.get("education_level"),
        course_type=profile.get("course_type"),
        requested_loan=profile.get("requested_loan"),
    )
    db.add(check)
    db.flush()

    english_results = []
    for i, r in enumerate(results[:3]):
        scheme = db.query(Scheme).filter(Scheme.id == r["scheme_id"]).first()
        if scheme is None:
            continue
        r["scheme_name"] = scheme.name
        r["scheme_slug"] = scheme.slug
        r["category"] = scheme.category
        r["max_loan"] = scheme.max_loan
        r["interest_rate"] = scheme.interest_rate
        r["tenure_months"] = scheme.tenure_months
        r["moratorium_months"] = scheme.moratorium_months
        r["income_threshold"] = scheme.income_threshold
        r["purpose"] = scheme.purpose
        r["is_demo"] = scheme.is_demo
        r["source_name"] = scheme.source_name
        r["source_url"] = scheme.source_url
        r["official_scheme_url"] = scheme.official_scheme_url
        r["official_apply_url"] = scheme.official_apply_url
        r["last_verified"] = scheme.last_verified
        r["source_type"] = scheme.source_type
        r["verification_status"] = scheme.verification_status
        english_results.append(r)

        lang = profile.get("language", "en")
        if i == 0:
            explanation_lang = "hi" if lang == "hi" else "en"
            explanation = ai_service.generate_recommendation_explanation(
                profile, r, explanation_lang
            )
            db.add(
                Recommendation(
                    eligibility_check_id=check.id,
                    scheme_id=scheme.id,
                    match_score=r["match_score"],
                    eligibility_status=r["eligibility_status"],
                    matched_criteria=json.dumps(r["matched"]),
                    unmatched_criteria=json.dumps(r["unmatched"]),
                    warnings=json.dumps(r["warnings"]),
                    reasons=json.dumps(r["reasons"]),
                    next_steps=json.dumps(_build_next_steps(r)),
                    ai_explanation=explanation,
                )
            )
            r["ai_explanation"] = explanation

    db.add(AuditEvent(event_type="recommendation", payload=f"checks={len(results)}"))
    db.commit()

    return {"profile": profile, "results": english_results}


def _build_next_steps(result: dict) -> list[str]:
    status = result.get("eligibility_status")
    steps = []
    if status in ("eligible", "conditional"):
        steps.append("Compare with other suitable schemes.")
        steps.append("Estimate the EMI with the financial calculator.")
        steps.append("Find an eligible nearby channel partner.")
        steps.append("Review the document checklist.")
        steps.append("Follow the application guidance to route your application.")
    else:
        steps.append("Review the unmatched criteria and revisit your profile.")
        steps.append("Explore alternative schemes that may match.")
        steps.append("Keep official scheme guidelines handy for verification.")
    return steps