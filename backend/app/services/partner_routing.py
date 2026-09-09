"""
Transparent weighted partner routing.

Weights:
    scheme compatibility  = 30
    distance suitability  = 20
    status / capacity     = 10
    eligibility category  = 40

Scores are computed deterministically and explained to the user.
"""

import math

from sqlalchemy.orm import Session

from app.models import Partner, Scheme

WEIGHTS = {
    "scheme": 30,
    "distance": 20,
    "capacity": 10,
    "eligibility": 40,
}


def haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    try:
        lat1, lon1, lat2, lon2 = (
            float(lat1),
            float(lon1),
            float(lat2),
            float(lon2),
        )
    except (TypeError, ValueError):
        return None
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def score_partner(partner: Partner, profile: dict, db: Session) -> dict:
    points = {"scheme": 0, "distance": 0, "capacity": 0, "eligibility": 0}
    notes = []

    scheme = None
    scheme_id = profile.get("scheme_id")
    if scheme_id:
        scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()

    # ---- Scheme compatibility (30) ----
    if scheme is not None:
        if scheme in partner.schemes:
            points["scheme"] = WEIGHTS["scheme"]
            notes.append("Scheme supported.")
        else:
            notes.append("Scheme not supported.")
    else:
        p_purpose = profile.get("purpose")
        if p_purpose and partner.type in ("PSB", "SCA", "NBFC-MFI"):
            points["scheme"] = WEIGHTS["scheme"]
            notes.append("Broad scheme coverage for this loan category (demo).")

    # ---- Distance (20) ----
    distance = haversine(
        profile.get("latitude"),
        profile.get("longitude"),
        partner.latitude,
        partner.longitude,
    )
    if distance is None:
        if profile.get("district") and partner.district == profile.get("district"):
            points["distance"] = WEIGHTS["distance"]
            notes.append("Same-district partner.")
        elif profile.get("state") and partner.state == profile.get("state"):
            points["distance"] = 14
            notes.append("Same-state partner.")
        else:
            points["distance"] = 4
            notes.append("Location match not verified.")
        distance = None
    elif distance <= 15:
        points["distance"] = WEIGHTS["distance"]
        notes.append("Strong location match (within ~15 km).")
    elif distance <= 50:
        points["distance"] = 13
        notes.append("Reasonable location match.")
    else:
        points["distance"] = 6
        notes.append("Distant partner.")

    # ---- Status / capacity (10) ----
    accepting = partner.accepting_applications and partner.status != "unavailable"
    if accepting and partner.status == "accepting":
        points["capacity"] = WEIGHTS["capacity"]
        notes.append("Currently accepting demo applications.")
    elif accepting and partner.status == "limited":
        points["capacity"] = 6
        notes.append("Limited capacity (demo status).")
    elif not accepting:
        points["capacity"] = 0
        notes.append("Temporarily unavailable.")

    # ---- Eligibility / category (40) ----
    purpose = profile.get("purpose")
    loan_amount = profile.get("loan_amount")
    if purpose == "education":
        if partner.type in ("PSB", "SCA"):
            points["eligibility"] = WEIGHTS["eligibility"]
            notes.append("Eligible for the education loan category.")
        elif partner.type in ("RRB",):
            points["eligibility"] = 30
            notes.append("Conditionally eligible for education category (demo).")
        else:
            points["eligibility"] = 20
            notes.append("Limited eligibility for education category (demo).")
    else:
        if partner.type in ("PSB", "SCA", "NBFC-MFI"):
            points["eligibility"] = WEIGHTS["eligibility"]
            notes.append("Eligible for this loan category.")
        elif partner.type == "RRB":
            points["eligibility"] = 34
            notes.append("Eligible with regional focus.")
        else:
            points["eligibility"] = 25
            notes.append("Category eligibility to be verified (demo).")

    total = sum(points.values())

    return {
        "partner": partner,
        "scheme_id": scheme_id,
        "points": points,
        "total": total,
        "notes": notes,
        "distance_km": round(distance, 1) if distance is not None else None,
    }


def route_partners(profile: dict, db: Session) -> list[dict]:
    query = db.query(Partner)
    if profile.get("state"):
        query = query.filter(Partner.state == profile["state"])
    partners = query.all()
    scored = []
    for partner in partners:
        scored.append(score_partner(partner, profile, db))
    scored.sort(key=lambda s: s["total"], reverse=True)
    return scored
