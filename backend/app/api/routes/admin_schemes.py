from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser, Scheme
from app.repositories.repositories import SchemeRepository
from app.schemas.schemas import SchemeCreate, SchemeOut, SchemeUpdate

router = APIRouter(tags=["admin-schemes"])


@router.get("", response_model=list[SchemeOut])
def list_schemes(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    schemes = SchemeRepository.list(db)
    return [admin_scheme_dict(s) for s in schemes]


@router.post("", response_model=SchemeOut)
def create_scheme(
    payload: SchemeCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    if SchemeRepository.get_by_slug(db, payload.slug):
        raise HTTPException(status_code=400, detail="Slug already exists")
    scheme = SchemeRepository.create(db, payload)
    return admin_scheme_dict(scheme)


@router.put("/{scheme_id}", response_model=SchemeOut)
def update_scheme(
    scheme_id: int,
    payload: SchemeUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    scheme = SchemeRepository.get(db, scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    scheme = SchemeRepository.update(db, scheme, payload.model_dump(exclude_none=True))
    return admin_scheme_dict(scheme)


@router.delete("/{scheme_id}")
def delete_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    scheme = SchemeRepository.get(db, scheme_id)
    if scheme is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    SchemeRepository.delete(db, scheme)
    return {"ok": True}


def admin_scheme_dict(s: Scheme) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "slug": s.slug,
        "description": s.description,
        "category": s.category,
        "purpose": s.purpose,
        "max_loan": s.max_loan,
        "min_loan": s.min_loan,
        "interest_rate": s.interest_rate,
        "tenure_months": s.tenure_months,
        "moratorium_months": s.moratorium_months,
        "income_threshold": s.income_threshold,
        "project_min": s.project_min,
        "project_max": s.project_max,
        "education_focus": s.education_focus,
        "eligibility_notes": s.eligibility_notes,
        "required_documents": s.required_documents,
        "partner_required": s.partner_required,
        "active": s.active,
        "is_demo": s.is_demo,
        "short_name": s.short_name,
        "provider": s.provider,
        "sub_category": s.sub_category,
        "target_groups": s.target_groups,
        "occupation_groups": s.occupation_groups,
        "gender_rule": s.gender_rule,
        "age_min": s.age_min,
        "age_max": s.age_max,
        "income_limit": s.income_limit,
        "state_scope": s.state_scope,
        "district_scope": s.district_scope,
        "education_requirements": s.education_requirements,
        "course_type": s.course_type,
        "business_sectors": s.business_sectors,
        "project_cost_min": s.project_cost_min,
        "project_cost_max": s.project_cost_max,
        "min_loan_amount": s.min_loan_amount,
        "max_loan_amount": s.max_loan_amount,
        "finance_percentage": s.finance_percentage,
        "beneficiary_contribution_percentage": s.beneficiary_contribution_percentage,
        "interest_rate_type": s.interest_rate_type,
        "interest_tiers": s.interest_tiers,
        "moratorium": s.moratorium,
        "repayment_period": s.repayment_period,
        "repayment_unit": s.repayment_unit,
        "application_mode": s.application_mode,
        "official": s.official,
        "data_confidence": s.data_confidence,
        "is_loan": s.is_loan,
        "source_name": s.source_name,
        "source_url": s.source_url,
        "official_scheme_url": s.official_scheme_url,
        "official_apply_url": s.official_apply_url,
        "last_verified": s.last_verified,
        "source_type": s.source_type,
        "verification_status": s.verification_status,
        "document_keys": [d.key for d in s.documents],
        "rules": [
            {"key": r.rule_key, "value": r.rule_value, "description": r.description}
            for r in s.rules
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
            for p in s.partners
        ],
    }