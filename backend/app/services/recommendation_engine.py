"""
Deterministic, transparent official-scheme recommendation engine.

Part 3 design:
- Hard filters A–H silently exclude incompatible schemes (yield score 0).
- A transparent 100-point score is produced for every non-excluded scheme:
    eligibility fit          40  = income 15 + gender 10 + age 8 + area 7
    purpose/education compat 25  = alignment 15 + sector 10
    amount compat            15
    targeted benefit fit     10  = category 6 + occupation 4
    geographic fit           10
- Eligibility status uses the three values the frontend knows
  (eligible | conditional | not_eligible). Finer "more_info_needed" cases are
  surfaced through warnings + verification_items instead of a new status value.
- Support programmes (PM-DAKSH, PM-AJAY; is_loan=False) are never loan
  recommendations; they are returned separately as "complementary_support".
- Never fabricate figures: missing/uncertain values are surfaced as
  warnings / verification items, and tiered interest is reported with its
  type + tiers (never invented as a single 0% figure).
- The result records carry the scheme display metadata inline so callers do
  not need a follow-up query per scheme (no N+1).
"""

from sqlalchemy.orm import Session, selectinload

from app.models import Scheme

# ---------------------------------------------------------------------------
# Weights (kept as explicit constants for transparency)
# ---------------------------------------------------------------------------
ELIGIBILITY_WEIGHTS = {"income": 15, "gender": 10, "age": 8, "area": 7}
PURPOSE_WEIGHTS = {"align": 15, "sector": 10}
AMOUNT_WEIGHT = 15
TARGETED_WEIGHTS = {"category": 6, "occupation": 4}
GEO_WEIGHT = 10

PURPOSES_EDUCATION = {"education"}
PURPOSES_BUSINESS = {
    "business",
    "self_employment",
    "business_expansion",
    "equipment",
    "working_capital",
    "skill_training",
}

FEMALE = {"female", "f", "woman", "women"}
MALE = {"male", "m"}

# Confidence → user-facing note (spec: verified vs needs_review messaging)
CONFIDENCE_NOTE = {
    "verified": (
        "Based on the current official-source data stored in Saksham, this scheme "
        "aligns with the profile you provided. Government terms can change — "
        "re-confirm on the official scheme portal before starting an application."
    ),
    "needs_review": (
        "Potential match — verify the latest official conditions on the official "
        "scheme portal before applying; the source data for this scheme is marked "
        "'needs review'."
    ),
    "demo": (
        "This is an indicative demo assessment. Confirm official eligibility and "
        "terms before applying."
    ),
}


def _fmt(value) -> str:
    """Format a number as an INR string, avoiding mangled unicode on old consoles."""
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "not specified"


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _confidence_note(scheme: Scheme) -> str:
    key = scheme.data_confidence or scheme.verification_status or "demo"
    if key not in CONFIDENCE_NOTE:
        key = "demo"
    return CONFIDENCE_NOTE[key]


def _scheme_is_education(scheme: Scheme) -> bool:
    return (
        scheme.category == "education"
        or (scheme.sub_category or "").lower() in ("education loan", "education")
    )


def _scheme_is_business(scheme: Scheme) -> bool:
    if _scheme_is_education(scheme):
        return False
    return scheme.category in ("business", "micro_finance", "term_loan") or (
        scheme.sub_category or ""
    ).lower() in ("micro finance", "micro credit", "term loan", "sanitation enterprise",
                  "green enterprise")


# ---------------------------------------------------------------------------
# Attribute matching helpers
# ---------------------------------------------------------------------------
def _category_matches_target(category: str, tg: str) -> bool:
    """Does the user's social category satisfy one scheme target-group label?"""
    tgl = _norm(tg)
    cat = _norm(category)
    if not cat or not tgl:
        return False
    # Scheduled Castes
    if ("scheduled caste" in tgl or tgl in ("sc", "scheduled castes")) and (
        cat in ("sc", "scheduled caste", "scheduled castes", "scheduledcaste")
        or "scheduled caste" in cat
    ):
        return True
    # Backward Classes / OBC
    if ("backward class" in tgl or tgl in ("obc", "bc", "other backward classes")) and (
        cat in ("obc", "bc", "backward class", "backward classes", "other backward classes")
        or "backward" in cat or "other backward" in cat
    ):
        return True
    # EBC
    if ("economically backward" in tgl or tgl == "ebc") and (
        cat in ("ebc", "economically backward classes") or "economically backward" in cat
    ):
        return True
    # Scheduled Tribes
    if ("scheduled tribe" in tgl or tgl in ("st", "scheduled tribes")) and (
        cat in ("st", "scheduled tribe", "scheduled tribes") or "scheduled tribe" in cat
    ):
        return True
    # De-notified / Nomadic / Semi-Nomadic
    if ("denotified" in tgl or "nomadic" in tgl or "semi-nomadic" in tgl or tgl == "dnt") and (
        "denotified" in cat or "nomadic" in cat or "dnt" in cat or "semi-nomadic" in cat
    ):
        return True
    return False


def _occupation_matches_target(profile, tg: str) -> bool:
    """Does the user's occupation satisfy a sanitation/occupation-based label?"""
    tgl = _norm(tg)
    occ = _norm(profile.get("occupation"))
    biz_type = _norm(profile.get("business_type"))
    cat = _norm(profile.get("category"))
    if not tgl:
        return False
    sanitation = ("safai" in tgl or "sanitation" in tgl or "karamchar" in tgl
                  or "sewage" in tgl or "clean" in tgl)
    if sanitation and ("safai" in occ or "sanitation" in occ or "karamchar" in occ
                       or "sewage" in occ or "cleaning" in occ or "cleaner" in occ):
        return True
    if "dependent" in tgl and (
        "dependent" in occ or "depend" in occ or "family" in occ or "child" in occ
    ):
        return True
    if "self-help group" in tgl or tgl == "shg":
        if "self help group" in occ or "shg" in occ or "self-help" in biz_type or "shg" in biz_type:
            return True
        if profile.get("gender") and _norm(profile.get("gender")) in FEMALE and "women" in tgl:
            return True
    return False


def _target_group_state(profile, scheme: Scheme):
    """
    Returns (hard_fail_reason | None, known: bool, matched: bool).
    Unknown attributes never hard-fail; they only downgrade the targeted score.
    """
    tgs = [t for t in (scheme.target_groups or []) if t]
    if not tgs:
        return None, True, True
    gender = _norm(profile.get("gender"))
    matched = []
    for tg in tgs:
        tgl = _norm(tg)
        if _category_matches_target(profile.get("category") or "", tg):
            matched.append(tg)
        elif "women" in tgl and gender in FEMALE:
            matched.append(tg)
        elif _occupation_matches_target(profile, tg):
            matched.append(tg)
        elif tgl == "general" and _norm(profile.get("category")) == "general":
            matched.append(tg)
    known = bool(
        profile.get("category") or profile.get("occupation") or profile.get("gender")
    )
    if matched:
        return None, known, True
    if known:
        return (
            f"This scheme targets {', '.join(map(str, tgs))} — your provided profile "
            f"(category/gender/occupation) does not match."
        ), known, False
    return None, known, False


def _occupation_group_state(profile, scheme: Scheme):
    """Occupation-based targeting (e.g. NSKFDC Safai Karamcharis)."""
    ogs = [o for o in (scheme.occupation_groups or []) if o]
    if not ogs:
        return None, True, True
    matched = [o for o in ogs if _occupation_matches_target(profile, o)]
    # Also allow category-based overlap (e.g. "Non-creamy layer Backward Classes")
    for o in ogs:
        tgl = _norm(o)
        if "non-creamy" in tgl and "backward" in tgl and _category_matches_target(
            profile.get("category") or "", "obc"
        ):
            matched.append(o)
    known_occupied = bool(profile.get("occupation") or profile.get("business_type"))
    if matched:
        return None, True, True
    if known_occupied:
        return (
            f"This scheme is occupation-based ({', '.join(map(str, ogs))}) — your "
            "provided occupation does not match."
        ), True, False
    # Unknown occupation: never silently fail, surface as a verification item.
    return None, False, False


def _gender_matches(profile, scheme: Scheme) -> tuple[bool | None, str | None]:
    rule = _norm(scheme.gender_rule)
    if rule in ("female", "women", "woman"):
        g = _norm(profile.get("gender"))
        if g in FEMALE:
            return True, None
        if g in MALE:
            return False, f"This scheme is for women only (gender rule: {scheme.gender_rule})."
        return None, None  # unknown gender
    return True, None


# ---------------------------------------------------------------------------
# Purpose / sector / education compatibility
# ---------------------------------------------------------------------------
def _purpose_block(profile, scheme: Scheme) -> str | None:
    user_purpose = _norm(profile.get("purpose"))
    scheme_edu = _scheme_is_education(scheme)
    if user_purpose in PURPOSES_EDUCATION and not scheme_edu:
        return "This is an educational-loan scheme unless you selected an education purpose. "
    if user_purpose not in PURPOSES_EDUCATION and scheme_edu:
        return "Your purpose is business-related — this scheme is an education-loan scheme."
    if user_purpose not in PURPOSES_EDUCATION | PURPOSES_BUSINESS and user_purpose:
        return f"Purpose '{profile.get('purpose')}' is not recognised as business or education."
    return None


def _purpose_align_score(profile, scheme: Scheme) -> tuple[float, str]:
    user_purpose = _norm(profile.get("purpose"))
    scheme_purpose = _norm(scheme.purpose or "")
    if user_purpose == scheme_purpose:
        return PURPOSE_WEIGHTS["align"], f"Your purpose ({user_purpose}) matches this scheme's purpose."
    if user_purpose in PURPOSES_EDUCATION and _scheme_is_education(scheme):
        return PURPOSE_WEIGHTS["align"], "Your purpose (education) matches this educational loan scheme."
    if user_purpose in PURPOSES_BUSINESS and scheme_purpose in ("business", "self_employment"):
        if user_purpose == "self_employment" and scheme_purpose == "business":
            return PURPOSE_WEIGHTS["align"] - 2, "Your self-employment goal fits this business scheme (slightly broader)."
        if user_purpose == "business" and scheme_purpose == "self_employment":
            return PURPOSE_WEIGHTS["align"] - 2, "Your business goal fits this self-employment scheme (slightly narrower)."
        if user_purpose in ("working_capital", "equipment", "business_expansion"):
            return PURPOSE_WEIGHTS["align"], "Your stated purpose aligns with this business finance scheme."
        if user_purpose == "skill_training":
            return PURPOSE_WEIGHTS["align"] - 3, "Skill training support aligns with this livelihood scheme (confirm fit on portal)."
        return PURPOSE_WEIGHTS["align"], "Your business purpose aligns with this scheme."
    return 0.0, "Purpose could not be aligned with this scheme."


def _sector_state(profile, scheme: Scheme) -> tuple[float, list[str], list[str], list[str], str | None]:
    """
    Business sector / education course-type fit. A *known* mismatch with an
    explicit scheme restriction downgrades considerably and is listed under
    unmatched; it is not a silent hard block (sector coverage wording varies).
    """
    matched, unmatched, warnings, items = [], [], [], []
    user_purpose = _norm(profile.get("purpose"))

    if user_purpose in PURPOSES_EDUCATION:
        course_types = [c for c in (scheme.course_type or []) if c]
        if not course_types:
            return PURPOSE_WEIGHTS["sector"], matched, unmatched, warnings, None
        usr = _norm(profile.get("course_type"))
        if usr and any(usr in _norm(c) or _norm(c) in usr for c in course_types):
            matched.append(f"Course type ({profile.get('course_type')}) is covered by this scheme.")
            return PURPOSE_WEIGHTS["sector"], matched, unmatched, warnings, None
        if usr:
            unmatched.append(
                f"Course type '{profile.get('course_type')}' is not listed for this scheme "
                f"({', '.join(course_types)})."
            )
            return PURPOSE_WEIGHTS["sector"] - 6, matched, unmatched, warnings, None
        items.append("Confirm your course/institution type appears in the scheme's eligible list.")
        return PURPOSE_WEIGHTS["sector"] - 5, matched, unmatched, warnings, None

    sectors = [s for s in (scheme.business_sectors or []) if s]
    if not sectors:
        return PURPOSE_WEIGHTS["sector"], matched, unmatched, warnings, None
    usr = _norm(profile.get("business_sector"))
    if usr:
        if any(usr in _norm(s) or _norm(s) in usr for s in sectors):
            matched.append(f"Business sector ({profile.get('business_sector')}) is supported by this scheme.")
            return PURPOSE_WEIGHTS["sector"], matched, unmatched, warnings, None
        unmatched.append(
            f"Business sector '{profile.get('business_sector')}' is outside this scheme's "
            f"supported list ({', '.join(sectors)})."
        )
        return PURPOSE_WEIGHTS["sector"] - 6, matched, unmatched, warnings, None
    items.append("Confirm your business sector is among the scheme's supported sectors.")
    return PURPOSE_WEIGHTS["sector"] - 5, matched, unmatched, warnings, None


# ---------------------------------------------------------------------------
# Amount compatibility (partial funding is NOT a hard block)
# ---------------------------------------------------------------------------
def _amount_state(profile, scheme: Scheme) -> tuple[float, list[str], list[str], list[str]]:
    matched, unmatched, warnings = [], [], []
    requested = (
        profile.get("requested_loan")
        or profile.get("project_cost")
        or profile.get("education_cost")
    )
    max_loan = (scheme.max_loan or 0) or (scheme.max_loan_amount or 0)
    if not requested:
        warnings.append("No requested amount provided — compare your need against the scheme limit.")
        return AMOUNT_WEIGHT - 5, matched, unmatched, warnings
    if max_loan <= 0:
        matched.append("Financing limit will be confirmed directly with the official authority.")
        return AMOUNT_WEIGHT, matched, unmatched, warnings
    if requested <= max_loan:
        matched.append(
            f"Requested amount ({_fmt(requested)}) is within the {_fmt(max_loan)} scheme maximum."
        )
        return AMOUNT_WEIGHT, matched, unmatched, warnings
    # Partial funding: not a silent block, but reduce the amount score.
    warnings.append(
        f"Scheme maximum assistance ({_fmt(max_loan)}) may not cover the full requested amount "
        f"({_fmt(requested)}) — explore a combination or confirm partial financing on the portal."
    )
    return AMOUNT_WEIGHT - 9, matched, unmatched, warnings


# ---------------------------------------------------------------------------
# Geographic fit
# ---------------------------------------------------------------------------
def _geo_state(profile, scheme: Scheme) -> tuple[float, list[str], list[str], str | None]:
    matched, warnings = [], []
    scope = [s for s in (scheme.state_scope or []) if s]
    if not scope or any(_norm(s) in ("nationwide", "all india", "all-india", "india") for s in scope):
        matched.append("This scheme operates nationwide.")
        return GEO_WEIGHT, matched, warnings, None
    usr = _norm(profile.get("state"))
    if usr:
        if any(_norm(s) == usr or usr in _norm(s) or _norm(s) in usr for s in scope):
            matched.append(f"Scheme operates in your state ({profile.get('state')}).")
            return GEO_WEIGHT, matched, warnings, None
        return GEO_WEIGHT - 8, matched, warnings, (
            f"This scheme's state scope ({', '.join(map(str, scope))}) does not include "
            f"your state ({profile.get('state')})."
        )
    warnings.append("State not provided — geographic eligibility could not be confirmed.")
    return GEO_WEIGHT - 5, matched, warnings, None


# ---------------------------------------------------------------------------
# Main matcher
# ---------------------------------------------------------------------------
def compute_match(profile: dict, scheme: Scheme) -> dict:
    """Compute a single scheme's match for a user profile (full result dict)."""
    reasons = []
    matched = []
    unmatched = []
    warnings = []
    verification_items = []

    # ---------------- Hard filters (silent when failed) ----------------
    hard_reasons = []

    purpose_block = _purpose_block(profile, scheme)
    if purpose_block:
        hard_reasons.append(purpose_block)

    income_limit = scheme.income_limit if scheme.income_limit is not None else scheme.income_threshold
    user_income = profile.get("annual_family_income")
    income_known = user_income is not None
    if income_limit is not None and income_known and user_income > income_limit:
        hard_reasons.append(
            f"Annual family income ({_fmt(user_income)}) exceeds the {_fmt(income_limit)} "
            "ceiling for this scheme."
        )

    gender_ok, gender_reason = _gender_matches(profile, scheme)
    if gender_ok is False:
        hard_reasons.append(gender_reason)

    age = profile.get("age")
    if scheme.age_min is not None and age is not None and age < scheme.age_min:
        hard_reasons.append(f"Minimum age for this scheme is {scheme.age_min}.")
    if scheme.age_max is not None and age is not None and age > scheme.age_max:
        hard_reasons.append(f"Maximum age for this scheme is {scheme.age_max}.")

    tg_fail, tg_known, tg_matched_any = _target_group_state(profile, scheme)
    if tg_fail:
        hard_reasons.append(tg_fail)

    oc_fail, oc_known, oc_matched_any = _occupation_group_state(profile, scheme)
    if oc_fail:
        hard_reasons.append(oc_fail)

    education_location_fail = None
    if _scheme_is_education(scheme):
        tiers = [t for t in (scheme.interest_tiers or []) if isinstance(t, dict)]
        locs = {_norm(t.get("course_location") or "") for t in tiers if t.get("course_location")}
        if locs:
            usr_loc = _norm(profile.get("education_location"))
            if usr_loc:
                if not any(usr_loc in l or l in usr_loc for l in locs):
                    education_location_fail = (
                        f"This scheme's course-location options ({', '.join(sorted(locs))}) "
                        f"do not include '{profile.get('education_location')}'."
                    )

    # District-level scope (rarely set) — silent when matched, downgraded when unknown
    area_score = ELIGIBILITY_WEIGHTS["area"]
    dscope = [d for d in (scheme.district_scope or []) if d]
    if dscope:
        usr_dist = _norm(profile.get("district"))
        if usr_dist:
            if any(_norm(d) == usr_dist or usr_dist in _norm(d) or _norm(d) in usr_dist for d in dscope):
                matched.append("Your district is covered by this scheme.")
            else:
                hard_reasons.append(
                    f"This scheme is limited to districts: {', '.join(map(str, dscope))}."
                )
        else:
            warnings.append("District scope is set for this scheme — district not provided.")
            area_score = max(0, area_score - 3)

    if education_location_fail:
        hard_reasons.append(education_location_fail)

    hard_block = bool(hard_reasons) or _purpose_block(profile, scheme) is not None

    # "H. Amount" is intentionally NOT a silent block — partial funding is fine.
    # ---------------- Scoring (only when not hard-blocked) ----------------
    if hard_block:
        return {
            "scheme_id": scheme.id,
            "match_score": 0.0,
            "eligibility_status": "not_eligible",
            "hard_block": True,
            "reasons": [],
            "match_reasons": [],
            "matched": [],
            "unmatched": hard_reasons,
            "warnings": warnings,
            "verification_items": [],
            "financing_summary": [],
            "repayment_financing": [],
            "recommendation_note": _confidence_note(scheme),
            "data_confidence": scheme.data_confidence or scheme.verification_status or "demo",
            "score_breakdown": {
                "eligibility": 0.0,
                "purpose": 0.0,
                "amount": 0.0,
                "targeted": 0.0,
                "geo": 0.0,
            },
            **(_scheme_fields(scheme)),
        }

    # ---- 1. Eligibility fit (40) ----
    el = {"income": 0.0, "gender": 0.0, "age": 0.0, "area": 0.0}

    if income_limit is None:
        el["income"] = ELIGIBILITY_WEIGHTS["income"]
        matched.append("No income ceiling imposes a restriction for this scheme.")
    elif income_known and user_income <= income_limit:
        el["income"] = ELIGIBILITY_WEIGHTS["income"]
        matched.append(
            f"Annual family income ({_fmt(user_income)}) is within the {_fmt(income_limit)} ceiling."
        )
        reasons.append("Income falls within the scheme's family-income ceiling.")
    else:
        el["income"] = ELIGIBILITY_WEIGHTS["income"] / 2
        warnings.append(
            f"Income not provided — verify against the {_fmt(income_limit)} ceiling "
            "for this scheme."
        )

    if gender_ok:
        if scheme.gender_rule:
            el["gender"] = ELIGIBILITY_WEIGHTS["gender"]
            matched.append(f"Gender criterion ({scheme.gender_rule}) is satisfied.")
        else:
            el["gender"] = ELIGIBILITY_WEIGHTS["gender"]
            matched.append("No gender restriction applies to this scheme.")
    else:
        el["gender"] = ELIGIBILITY_WEIGHTS["gender"] / 2
        warnings.append("Gender not provided — confirm against this scheme's women-only preference.")

    age_bounds = scheme.age_min is not None or scheme.age_max is not None
    if age_bounds and age is not None:
        el["age"] = ELIGIBILITY_WEIGHTS["age"]
        matched.append("Your age is within this scheme's range.")
    elif age_bounds:
        el["age"] = ELIGIBILITY_WEIGHTS["age"] / 2
        warnings.append(f"Age not provided — this scheme has age limits (min {scheme.age_min}, max {scheme.age_max}).")
    else:
        el["age"] = ELIGIBILITY_WEIGHTS["age"]
        matched.append("No age restriction applies to this scheme.")

    el["area"] = area_score

    # ---- 2. Purpose / education compatibility (25) ----
    align, align_reason = _purpose_align_score(profile, scheme)
    p_matched, p_unmatched, p_warnings, p_items = [], [], [], []
    sector, p_m, p_u, p_w, p_i = _sector_state(profile, scheme)
    p_matched.extend(p_m); p_unmatched.extend(p_u); p_warnings.extend(p_w)
    if p_i:
        verification_items.append(p_i)
    matched.append(align_reason)
    reasons.append(align_reason)
    matched.extend(p_matched)
    unmatched.extend(p_unmatched)
    warnings.extend(p_warnings)

    purpose_score = align + sector

    # ---- 3. Amount compat (15) ----
    a_score, a_m, a_u, a_w = _amount_state(profile, scheme)
    matched.extend(a_m); unmatched.extend(a_u); warnings.extend(a_w)
    if any("may not cover" in w for w in a_w):
        financing_note = "Partial funding applies — the scheme may not cover your full requested amount."
    else:
        financing_note = "Amount is within the scheme limit (subject to official terms)."

    # ---- 4. Targeted benefit fit (10) ----
    tgt = {"category": 0.0, "occupation": 0.0}
    tgs = [t for t in (scheme.target_groups or []) if t]
    if not tgs:
        tgt["category"] = TARGETED_WEIGHTS["category"]
    elif tg_matched_any:
        tgt["category"] = TARGETED_WEIGHTS["category"]
        matched.append("Your profile matches this scheme's target group.")
    elif tg_known:
        tgt["category"] = TARGETED_WEIGHTS["category"] / 2
        unmatched.append("Confirm you belong to the scheme's target beneficiary group.")
    else:
        tgt["category"] = TARGETED_WEIGHTS["category"] / 3
        verification_items.append(f"Provide your social category — this scheme targets {', '.join(map(str, tgs))}.")

    ogs = [o for o in (scheme.occupation_groups or []) if o]
    if not ogs:
        tgt["occupation"] = TARGETED_WEIGHTS["occupation"]
    elif oc_matched_any:
        tgt["occupation"] = TARGETED_WEIGHTS["occupation"]
        matched.append("Your occupation matches this scheme's occupation-based targeting.")
    elif oc_known:
        tgt["occupation"] = TARGETED_WEIGHTS["occupation"] / 2
        unmatched.append("Confirm you belong to the scheme's occupation-based target group.")
    else:
        tgt["occupation"] = TARGETED_WEIGHTS["occupation"] / 3
        verification_items.append(
            "Confirm your occupation — this scheme is occupation-based "
            f"({', '.join(map(str, ogs))})."
        )

    # ---- 5. Geographic fit (10) ----
    geo, g_m, g_w, geo_unmatched = _geo_state(profile, scheme)
    matched.extend(g_m); warnings.extend(g_w)
    if geo_unmatched:
        unmatched.append(geo_unmatched)

    total = round(
        sum(el.values()) + purpose_score + a_score + sum(tgt.values()) + geo, 1
    )

    # Financing summary (strip leading markers)
    financing = [financing_note]
    if scheme.finance_percentage:
        financing.append(f"Scheme finances up to {scheme.finance_percentage:g}% of the project or course cost.")
    if scheme.beneficiary_contribution_percentage:
        financing.append(f"Beneficiary contribution expected: {scheme.beneficiary_contribution_percentage:g}%.")
    if scheme.interest_rate_type:
        financing.append(f"Interest: {_interest_display(scheme)}.")
    if scheme.repayment_period:
        financing.append(f"Repayment: {scheme.repayment_period}.")
    if scheme.moratorium:
        financing.append(f"Moratorium: {scheme.moratorium}.")

    # ---- Status (eligible / conditional / not_eligible — frontend-safe) ----
    if total >= 70:
        status = "eligible"
    elif total >= 40:
        status = "conditional"
    else:
        status = "not_eligible"

    return {
        "scheme_id": scheme.id,
        "match_score": total,
        "eligibility_status": status,
        "hard_block": False,
        "reasons": reasons[:8],
        "match_reasons": reasons[:8],
        "matched": matched,
        "unmatched": unmatched,
        "warnings": warnings,
        "verification_items": verification_items,
        "financing_summary": financing,
        "repayment_financing": financing,
        "recommendation_note": _confidence_note(scheme),
        "data_confidence": scheme.data_confidence or scheme.verification_status or "demo",
        "score_breakdown": {
            "eligibility": round(sum(el.values()), 1),
            "purpose": round(purpose_score, 1),
            "amount": round(a_score, 1),
            "targeted": round(sum(tgt.values()), 1),
            "geo": round(geo, 1),
        },
        **_scheme_fields(scheme),
    }


def _interest_display(scheme: Scheme) -> str:
    if scheme.interest_rate is not None:
        return f"{scheme.interest_rate:g}% p.a. ({scheme.interest_rate_type or 'fixed'})"
    tiers = scheme.interest_tiers or []
    rates = sorted(
        {
            float(t.get("interest_rate"))
            for t in tiers
            if isinstance(t, dict) and t.get("interest_rate") is not None
        }
    )
    if rates:
        lo, hi = rates[0], rates[-1]
        return f"tiered {lo:g}%–{hi:g}% p.a. (per official slabs)"
    return "confirmed on the official portal (tiered)"


def _scheme_fields(scheme: Scheme) -> dict:
    """Inline display metadata so callers avoid a per-scheme follow-up query."""
    return {
        "scheme_name": scheme.name,
        "scheme_slug": scheme.slug,
        "category": scheme.category,
        "sub_category": scheme.sub_category,
        "purpose": scheme.purpose,
        "max_loan": scheme.max_loan,
        "min_loan": scheme.min_loan,
        "interest_rate": scheme.interest_rate,
        "interest_rate_type": scheme.interest_rate_type,
        "interest_tiers": scheme.interest_tiers,
        "interest_display": _interest_display(scheme),
        "tenure_months": scheme.tenure_months,
        "moratorium_months": scheme.moratorium_months,
        "income_threshold": (
            scheme.income_limit
            if scheme.income_limit is not None
            else scheme.income_threshold
        ),
        "project_min": scheme.project_min,
        "project_max": scheme.project_max,
        "finance_percentage": scheme.finance_percentage,
        "is_loan": scheme.is_loan,
        "is_demo": scheme.is_demo,
        "source_name": scheme.source_name,
        "source_url": scheme.source_url,
        "official_scheme_url": scheme.official_scheme_url,
        "official_apply_url": scheme.official_apply_url,
        "last_verified": scheme.last_verified,
        "source_type": scheme.source_type,
        "verification_status": scheme.verification_status,
        "application_mode": scheme.application_mode,
    }


# ---------------------------------------------------------------------------
# Engine entry points
# ---------------------------------------------------------------------------
def _load_schemes(
    db: Session, official_only: bool, loan: bool, scheme_ids: list[int] | None = None
) -> list[Scheme]:
    query = db.query(Scheme).filter(
        Scheme.active.is_(True), Scheme.is_loan.is_(loan)
    )
    if official_only:
        query = query.filter(Scheme.is_demo.is_(False))
    if scheme_ids:
        query = query.filter(Scheme.id.in_(scheme_ids))
    # Eager-load partners + rules to avoid N+1 during scoring.
    return (
        query.options(selectinload(Scheme.partners), selectinload(Scheme.documents))
        .all()
    )


def compute_match_result(profile: dict, scheme: Scheme) -> dict:
    return compute_match(profile, scheme)


def recommend(
    profile: dict,
    db: Session,
    scheme_ids: list[int] | None = None,
    official_only: bool = False,
) -> list[dict]:
    """Return the primary (loan) matches, best-first. Backward-compatible list."""
    schemes = _load_schemes(db, official_only, loan=True, scheme_ids=scheme_ids)
    results = [compute_match(profile, s) for s in schemes]
    results = [r for r in results if r["match_score"] > 0]
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results


def recommend_full(
    profile: dict,
    db: Session,
    scheme_ids: list[int] | None = None,
    official_only: bool = True,
) -> dict:
    """Full response: primary loan matches + complementary (non-loan) support."""
    primary = recommend(profile, db, scheme_ids, official_only=official_only)

    support = []
    support_schemes = _load_schemes(db, official_only, loan=False, scheme_ids=scheme_ids)
    for s in support_schemes:
        purpose = _norm(profile.get("purpose"))
        if purpose in PURPOSES_BUSINESS:
            relevance = True
        else:
            relevance = False
        if not relevance:
            continue
        m = compute_match(profile, s)
        base = {"scheme_id": s.id, "scheme_name": s.name, "scheme_slug": s.slug,
                "match_score": m["match_score"], "eligibility_status": m["eligibility_status"],
                "hard_block": m["hard_block"], "reasons": [], "matched": [], "unmatched": [],
                "warnings": m["warnings"], "verification_items": m["verification_items"],
                "financing_summary": ["Additional Government Support — this is a support "
                                      "programme, not a loan. No financial cap applies."]}
        base.update(_scheme_fields(s))
        base["recommendation_note"] = m["recommendation_note"]
        support.append(base)

    no_match_reason = None
    if not primary:
        no_match_reason = (
            "No official loan scheme matched your profile as a hard-eligible target. "
            "Review the targeted group, income ceiling, gender/age rules, purpose and "
            "state scope, then retry."
        )

    return {
        "primary_matches": primary,
        "complementary_support": support,
        "results": primary,
        "no_match_reason": no_match_reason,
    }


def determine_best(profile: dict, db: Session, scheme_ids=None) -> dict | None:
    results = recommend(profile, db, scheme_ids)
    if not results:
        return None
    return results[0]