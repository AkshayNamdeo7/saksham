import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent, EligibilityCheck, Recommendation
from app.schemas.schemas import RecommendRequest
from app.services.ai_service import ai_service
from app.services.recommendation_engine import recommend_full

router = APIRouter(tags=["recommendations"])


@router.post("")
def get_recommendations(payload: RecommendRequest, db: Session = Depends(get_db)):
    profile = payload.profile.model_dump()
    # Always return official (non-demo) schemes for normal users.
    try:
        engine = recommend_full(profile, db, payload.scheme_ids, official_only=True)
    except Exception as exc:  # controlled error — no internals leak to clients
        raise HTTPException(
            status_code=400,
            detail="Recommendations could not be computed. Please try again with "
            "valid eligibility details.",
        ) from exc

    primary_matches = engine["primary_matches"]
    complementary_support = engine["complementary_support"]

    # persist eligibility check + top recommendation (extended profile stored as
    # a JSON summary in the existing result_summary column — no schema change)
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
        result_summary=json.dumps(
            {
                "gender": profile.get("gender"),
                "category": profile.get("category"),
                "occupation": profile.get("occupation"),
                "business_sector": profile.get("business_sector"),
                "business_type": profile.get("business_type"),
                "business_goal": profile.get("business_goal"),
                "education_location": profile.get("education_location"),
                "primary_matches": len(primary_matches),
                "complementary_support": len(complementary_support),
                "no_match_reason": engine["no_match_reason"],
            }
        ),
    )
    db.add(check)
    db.flush()

    english_results = []
    for i, r in enumerate(primary_matches[:10]):
        if r["match_score"] <= 0:
            continue
        english_results.append(r)

        if i == 0:
            lang = profile.get("language", "en")
            explanation_lang = "hi" if lang == "hi" else "en"
            explanation = ai_service.generate_recommendation_explanation(
                profile, r, explanation_lang
            )
            db.add(
                Recommendation(
                    eligibility_check_id=check.id,
                    scheme_id=r["scheme_id"],
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

    db.add(AuditEvent(event_type="recommendation", payload=f"checks={len(primary_matches)}"))
    db.commit()

    return {
        "profile": profile,
        "results": english_results,
        "primary_matches": english_results,
        "complementary_support": complementary_support,
        "no_match_reason": engine["no_match_reason"],
    }


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
