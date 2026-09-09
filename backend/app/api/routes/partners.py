from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Partner, Scheme
from app.schemas.schemas import PartnerOut

router = APIRouter(tags=["partners"])


@router.get("", response_model=list[PartnerOut])
def list_partners(
    state: str | None = None,
    district: str | None = None,
    type: str | None = None,
    status: str | None = None,
    scheme_id: int | None = None,
    accepting: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Partner)
    if state:
        q = q.filter(Partner.state == state)
    if district:
        q = q.filter(Partner.district == district)
    if type:
        q = q.filter(Partner.type == type)
    if status:
        q = q.filter(Partner.status == status)
    if accepting is not None:
        q = q.filter(Partner.accepting_applications == accepting)
    if scheme_id:
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if scheme is None:
            raise HTTPException(status_code=404, detail="Scheme not found")
        q = q.filter(Partner.schemes.any(Scheme.id == scheme_id))
    partners = q.all()
    return [serialize_partner(p) for p in partners]


@router.get("/{partner_id}", response_model=PartnerOut)
def get_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return serialize_partner(partner)


def serialize_partner(partner) -> dict:
    return {
        "id": partner.id,
        "name": partner.name,
        "type": partner.type,
        "state": partner.state,
        "district": partner.district,
        "city": partner.city,
        "address": partner.address,
        "latitude": partner.latitude,
        "longitude": partner.longitude,
        "status": partner.status,
        "capacity_pct": partner.capacity_pct,
        "fund_utilization_pct": partner.fund_utilization_pct,
        "npa_indicator": partner.npa_indicator,
        "phone": partner.phone,
        "email": partner.email,
        "accepting_applications": partner.accepting_applications,
        "is_demo": partner.is_demo,
        "scheme_slugs": [s.slug for s in partner.schemes],
        "supported_schemes": [
            {"id": s.id, "name": s.name, "slug": s.slug} for s in partner.schemes
        ],
    }