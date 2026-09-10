"""
Deterministic, transparent scheme recommendation engine.

Business rules are stored as structured Scheme + SchemeRule database rows.
This service reads configuration from the database (not hardcoded in the UI)
and produces a match score + explicit reasons.
"""

from sqlalchemy.orm import Session

from app.models import Scheme, SchemeRule


def _purpose_business(purpose: str) -> bool:
    return purpose in ("business", "self_employment")


def compute_match(profile: dict, scheme: Scheme) -> dict:
    """Compute a single scheme's match for a user profile."""
    reasons = []
    matched = []
    unmatched = []
    warnings = []
    score = 0.0
    max_score = 100.0

    purpose = profile.get("purpose", "")
    project_cost = profile.get("project_cost")
    annual_income = profile.get("annual_family_income")
    education_cost = profile.get("education_cost")
    education_level = profile.get("education_level")
    requested_loan = profile.get("requested_loan")

    scheme_purpose = getattr(scheme, "purpose", "")
    scheme_category = getattr(scheme, "category", "")
    is_official = not getattr(scheme, "is_demo", True)

    # ---- Purpose match (weight 30) ----
    is_education = purpose == "education"
    if is_education and scheme_category == "education":
        score += 30
        matched.append("Your purpose (education) matches the education scheme category.")
        reasons.append("Purpose matches an educational loan scheme.")
    elif (not is_education) and scheme_purpose == purpose:
        score += 30
        matched.append("Your purpose aligns with this scheme's intended use.")
        reasons.append(f"Purpose matches ({purpose}).")
    elif (not is_education) and scheme_category in ("micro_finance", "term_loan") and purpose in ("business", "self_employment"):
        score += 30
        matched.append("This scheme supports business/self-employment purposes.")
        reasons.append("Purpose matches a business/self-employment scheme.")
    else:
        unmatched.append("Scheme purpose does not match your selected purpose.")

    # ---- Income eligibility (weight 15) ----
    threshold = getattr(scheme, "income_threshold", None)
    if threshold is not None:
        if annual_income is not None and annual_income <= threshold:
            score += 15
            matched.append(
                f"Annual family income (₹{annual_income:,.0f}) is within the ₹{threshold:,.0f} threshold."
            )
            reasons.append("Income falls within the scheme income ceiling.")
        elif annual_income is None:
            warnings.append("Income not provided; verify against the applicable income threshold.")
        else:
            unmatched.append(
                f"Annual family income exceeds the ₹{threshold:,.0f} income threshold for this scheme."
            )
    else:
        score += 15
        matched.append("No specific income restriction configured for this scheme.")

    # ---- Project amount compatibility (weight 20) ----
    if not is_education:
        pmin = getattr(scheme, "project_min", None)
        pmax = getattr(scheme, "project_max", None)
        cost = project_cost
        if cost is None and requested_loan is not None:
            cost = requested_loan
        if cost is not None:
            if pmin is not None and cost < pmin:
                unmatched.append(f"Project cost is below the ₹{pmin:,.0f} minimum.")
            elif pmax is not None and cost > pmax:
                unmatched.append(f"Project cost exceeds the ₹{pmax:,.0f} maximum.")
            elif pmin is not None and pmax is not None and pmin <= cost <= pmax:
                score += 20
                matched.append(
                    f"Estimated project cost (₹{cost:,.0f}) is within the ₹{pmin:,.0f}–₹{pmax:,.0f} range."
                )
                reasons.append("Project cost is within the configured range.")
            elif pmax is not None and cost <= pmax:
                score += 20
                matched.append("Project cost is within the scheme limit.")
                reasons.append("Project cost is within the configured limit.")
            elif pmin is not None and cost >= pmin:
                score += 20
                matched.append("Project cost meets the minimum threshold.")
                reasons.append("Project cost meets the minimum threshold.")
            else:
                score += 15
                matched.append("Project cost has no specific band restriction in this scheme.")
        else:
            score += 20
            matched.append("No project cost conflict detected for this scheme.")
    else:
        if education_cost is not None:
            max_loan = getattr(scheme, "max_loan", 0) or 0
            if max_loan > 0 and education_cost <= max_loan:
                score += 20
                matched.append("Estimated education cost is within the financing limit.")
                reasons.append("Education expense is within the loan limit.")
            elif max_loan > 0:
                unmatched.append("Estimated education cost exceeds the financing limit.")
            else:
                score += 20
                matched.append("Education cost will be verified against official scheme limits.")
        else:
            score += 20
            matched.append("No education cost conflict detected for this scheme.")

    # ---- Loan limit validation (weight 15) ----
    max_loan = getattr(scheme, "max_loan", 0) or 0
    loan_need = requested_loan or project_cost or education_cost
    if max_loan > 0 and loan_need is not None and loan_need > max_loan:
        unmatched.append(
            f"Requested/estimated amount (₹{loan_need:,.0f}) exceeds the ₹{max_loan:,.0f} maximum."
        )
    elif max_loan > 0 and loan_need is not None:
        score += 15
        matched.append(f"Requested amount is within the ₹{max_loan:,.0f} maximum.")
    elif max_loan == 0 and is_official:
        score += 15
        matched.append("Loan limit to be confirmed on the official scheme portal.")
    else:
        score += 15
        matched.append("No loan amount conflict detected.")

    # ---- Education status (weight 5) ----
    if is_education:
        if education_level:
            score += 5
            matched.append("Education details captured for eligibility review.")
        else:
            warnings.append("Education details incomplete; confirm applicable course criteria.")
    else:
        score += 5
        matched.append("Education status is not a blocking criterion for this scheme.")

    # ---- Configurable criteria from SchemeRule rows ----
    extra_weights = {"category": 10, "custom": 5}
    for rule in scheme.rules:
        key = rule.rule_key
        val = rule.rule_value
        if key in ("purpose", "category"):
            if val in (scheme_purpose, scheme_category) or val == purpose:
                score += extra_weights.get("category", 10)
                matched.append(f"Matches configured criterion: {rule.description or key}.")
            else:
                unmatched.append(f"Does not match configured criterion: {key}.")
        elif key == "min_age":
            age = profile.get("age")
            if age is not None and age >= int(val):
                score += 5
            elif age is not None:
                unmatched.append(f"Minimum age {val} not met.")

    score = round(min(score, max_score), 1)

    # Derive eligibility status from score + hard blocks
    status = "eligible"
    hard_block = False
    if is_education and scheme_category != "education":
        status = "not_eligible"
        hard_block = True
    elif not is_education and scheme_category == "education":
        status = "not_eligible"
        hard_block = True
    elif any("exceeds" in u for u in unmatched) and score < 70:
        status = "not_eligible"
        hard_block = True
    elif score >= 70:
        status = "eligible"
    elif score >= 40:
        status = "conditional"
    else:
        status = "not_eligible"

    return {
        "scheme_id": scheme.id,
        "match_score": score,
        "eligibility_status": status,
        "hard_block": hard_block,
        "reasons": reasons[:5],
        "matched": matched,
        "unmatched": unmatched,
        "warnings": warnings,
    }


def recommend(
    profile: dict,
    db: Session,
    scheme_ids: list[int] | None = None,
    official_only: bool = False,
) -> list[dict]:
    query = db.query(Scheme).filter(Scheme.active.is_(True))
    if official_only:
        query = query.filter(Scheme.is_demo.is_(False))
    if scheme_ids:
        query = query.filter(Scheme.id.in_(scheme_ids))
    schemes = query.all()
    results = []
    for scheme in schemes:
        results.append(compute_match(profile, scheme))
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results


def determine_best(profile: dict, db: Session, scheme_ids=None) -> dict | None:
    results = recommend(profile, db, scheme_ids)
    if not results:
        return None
    return results[0]
