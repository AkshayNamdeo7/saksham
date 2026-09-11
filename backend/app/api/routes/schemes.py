from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Document, Partner, Scheme, SchemeRule
from app.schemas.schemas import DocumentOut, SchemeOut

router = APIRouter(tags=["schemes"])


@router.get("", response_model=list[SchemeOut])
def list_schemes(
    purpose: str | None = None,
    category: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Scheme).filter(Scheme.active.is_(True))
    if purpose:
        q = q.filter(Scheme.purpose == purpose)
    if category:
        q = q.filter(Scheme.category == category)
    if search:
        q = q.filter(
            (Scheme.name.ilike(f"%{search}%"))
            | (Scheme.description.ilike(f"%{search}%"))
        )
    schemes = q.all()
    return [serialize_scheme(s, db) for s in schemes]


@router.get("/{scheme_id}", response_model=SchemeOut)
def get_scheme(scheme_id: int, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return serialize_scheme(scheme, db)


@router.get("/{scheme_id}/documents", response_model=list[DocumentOut])
def scheme_documents(scheme_id: int, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme.documents


def serialize_scheme(scheme, db) -> dict:
    data = {
        "id": scheme.id,
        "name": scheme.name,
        "slug": scheme.slug,
        "description": scheme.description,
        "category": scheme.category,
        "purpose": scheme.purpose,
        "max_loan": scheme.max_loan,
        "min_loan": scheme.min_loan,
        "interest_rate": scheme.interest_rate,
        "tenure_months": scheme.tenure_months,
        "moratorium_months": scheme.moratorium_months,
        "income_threshold": scheme.income_threshold,
        "project_min": scheme.project_min,
        "project_max": scheme.project_max,
        "education_focus": scheme.education_focus,
        "eligibility_notes": scheme.eligibility_notes,
        "required_documents": scheme.required_documents,
        "partner_required": scheme.partner_required,
        "active": scheme.active,
        "is_demo": scheme.is_demo,
        "short_name": scheme.short_name,
        "provider": scheme.provider,
        "sub_category": scheme.sub_category,
        "target_groups": scheme.target_groups,
        "occupation_groups": scheme.occupation_groups,
        "gender_rule": scheme.gender_rule,
        "age_min": scheme.age_min,
        "age_max": scheme.age_max,
        "income_limit": scheme.income_limit,
        "state_scope": scheme.state_scope,
        "district_scope": scheme.district_scope,
        "education_requirements": scheme.education_requirements,
        "course_type": scheme.course_type,
        "business_sectors": scheme.business_sectors,
        "project_cost_min": scheme.project_cost_min,
        "project_cost_max": scheme.project_cost_max,
        "min_loan_amount": scheme.min_loan_amount,
        "max_loan_amount": scheme.max_loan_amount,
        "finance_percentage": scheme.finance_percentage,
        "beneficiary_contribution_percentage": scheme.beneficiary_contribution_percentage,
        "interest_rate_type": scheme.interest_rate_type,
        "interest_tiers": scheme.interest_tiers,
        "moratorium": scheme.moratorium,
        "repayment_period": scheme.repayment_period,
        "repayment_unit": scheme.repayment_unit,
        "application_mode": scheme.application_mode,
        "official": scheme.official,
        "data_confidence": scheme.data_confidence,
        "is_loan": scheme.is_loan,
        "source_name": scheme.source_name,
        "source_url": scheme.source_url,
        "official_scheme_url": scheme.official_scheme_url,
        "official_apply_url": scheme.official_apply_url,
        "last_verified": scheme.last_verified,
        "source_type": scheme.source_type,
        "verification_status": scheme.verification_status,
        "document_keys": [d.key for d in scheme.documents],
        "rules": [
            {"key": r.rule_key, "value": r.rule_value, "description": r.description}
            for r in scheme.rules
        ],
        "supported_partners": [
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "state": p.state,
                "district": p.district,
                "city": p.city,
                "status": p.status,
            }
            for p in scheme.partners
        ],
    }
    return data