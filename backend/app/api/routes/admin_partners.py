from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser, Document, Partner
from app.repositories.repositories import PartnerRepository
from app.schemas.schemas import PartnerCreate, PartnerOut, PartnerUpdate

router = APIRouter(tags=["admin-partners"])


@router.get("", response_model=list[PartnerOut])
def list_partners(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    return [admin_partner_dict(p) for p in PartnerRepository.list(db)]


@router.post("", response_model=PartnerOut)
def create_partner(
    payload: PartnerCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    partner = PartnerRepository.create(db, payload)
    return admin_partner_dict(partner)


@router.put("/{partner_id}", response_model=PartnerOut)
def update_partner(
    partner_id: int,
    payload: PartnerUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    partner = PartnerRepository.get(db, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    partner = PartnerRepository.update(db, partner, payload.model_dump(exclude_none=True))
    return admin_partner_dict(partner)


@router.delete("/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    partner = PartnerRepository.get(db, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    PartnerRepository.delete(db, partner)
    return {"ok": True}


def admin_partner_dict(p: Partner) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "type": p.type,
        "state": p.state,
        "district": p.district,
        "city": p.city,
        "address": p.address,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "status": p.status,
        "capacity_pct": p.capacity_pct,
        "fund_utilization_pct": p.fund_utilization_pct,
        "npa_indicator": p.npa_indicator,
        "phone": p.phone,
        "email": p.email,
        "accepting_applications": p.accepting_applications,
        "is_demo": p.is_demo,
        "scheme_slugs": [s.slug for s in p.schemes],
        "supported_schemes": [
            {"id": s.id, "name": s.name, "slug": s.slug} for s in p.schemes
        ],
    }