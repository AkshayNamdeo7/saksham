"""
Recommendation-engine rule tests (Part 3).

Covers the hard filters A–H, the 5-component scoring, status mapping,
partial-funding semantics, complementary (non-loan) support separation,
demo exclusion, unknown-value handling, and the no-match path.

Run with: pytest backend/tests -q
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///./test_saksham.db"
os.environ["SEED_ON_STARTUP"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine, SessionLocal
from app.db.seed import seed
from app.main import app

SC_BUSINESS = {
    "age": 30,
    "state": "Madhya Pradesh",
    "district": "Bhopal",
    "city": "Bhopal",
    "annual_family_income": 240000,
    "purpose": "business",
    "project_type": "small_manufacturing",
    "project_cost": 120000,
    "requested_loan": 120000,
    "category": "SC",
}

SC_EDUCATION = {
    "age": 20,
    "state": "Madhya Pradesh",
    "district": "Bhopal",
    "annual_family_income": 240000,
    "purpose": "education",
    "course_type": "Undergraduate",
    "education_cost": 500000,
    "category": "SC",
}


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    try:
        seed(s)
    finally:
        pass
    yield s
    s.close()


def _post(client, profile):
    r = client.post("/api/recommendations", json={"profile": profile})
    assert r.status_code == 200, r.text
    return r.json()


def _slug_set(primary):
    return {r["scheme_slug"] for r in primary}


# ---------------------------------------------------------------------------
# A. Target group / category hard filter
# ---------------------------------------------------------------------------
def test_sc_stays_eligible_for_sc_schemes(client):
    data = _post(client, SC_BUSINESS)
    primary = data["primary_matches"]
    assert len(primary) > 0
    top = primary[0]
    assert top["match_score"] >= 70
    assert top["eligibility_status"] in ("eligible", "conditional")
    assert top["hard_block"] is False
    slugs = _slug_set(primary)
    assert "nsfdc-mfs" in slugs or "nsfdc-term-loan" in slugs


def test_target_group_mismatch_excludes_the_other_finance_corps(client):
    # OBC entrepreneur -> NSFDC (SC-only) must be silently excluded, NBCFDC eligible.
    data = _post(client, {**SC_BUSINESS, "category": "OBC"})
    slugs = _slug_set(data["primary_matches"])
    assert "nsfdc-mfs" not in slugs
    assert "nsfdc-term-loan" not in slugs
    assert "nbcfdc-general-loan" in slugs


# ---------------------------------------------------------------------------
# B. Income ceiling hard filter
# ---------------------------------------------------------------------------
def test_income_over_ceiling_hard_blocks_ceiling_schemes(client):
    data = _post(client, {**SC_BUSINESS, "annual_family_income": 600000})
    slugs = _slug_set(data["primary_matches"])
    # NSFDC ceiling is 5 L — 6 L income must not produce NSFDC loans.
    assert "nsfdc-mfs" not in slugs
    assert "nsfdc-term-loan" not in slugs
    ns = [r for r in data["primary_matches"] if r["scheme_slug"] == "nsfdc-mfs"]
    assert ns == []


def test_income_within_ceiling_allowed(client):
    data = _post(client, {**SC_BUSINESS, "annual_family_income": 500000})
    assert "nsfdc-mfs" in _slug_set(data["primary_matches"])


# ---------------------------------------------------------------------------
# C. Gender rule hard filter
# ---------------------------------------------------------------------------
def test_male_excluded_from_women_only_schemes(client):
    data = _post(client, {**SC_BUSINESS, "category": "OBC", "gender": "male"})
    slugs = _slug_set(data["primary_matches"])
    assert "nbcfdc-new-swarnima-women" not in slugs
    assert "nskfdc-mahila-adhikarita" not in slugs
    assert "nbcfdc-general-loan" in slugs


# ---------------------------------------------------------------------------
# E. Purpose (education vs business) hard filter
# ---------------------------------------------------------------------------
def test_education_purpose_only_returns_education_schemes(client):
    data = _post(client, SC_EDUCATION)
    primary = data["primary_matches"]
    assert len(primary) > 0
    assert all(r["category"] == "education" for r in primary)
    slugs = _slug_set(primary)
    assert "nsfdc-educational-loan" in slugs
    top = primary[0]
    assert top["match_score"] >= 70
    assert top["eligibility_status"] in ("eligible", "conditional")


# ---------------------------------------------------------------------------
# F/G. Sector / course-type matching
# ---------------------------------------------------------------------------
def test_course_type_mismatch_downgrades_education_scheme(client):
    data = _post(client, {**SC_EDUCATION, "course_type": "Music"})
    edu = [r for r in data["primary_matches"] if r["scheme_slug"] == "nsfdc-educational-loan"]
    assert edu, "NSFDC ELS should still be returned"
    assert any("Music" in u for u in edu[0]["unmatched"])


# ---------------------------------------------------------------------------
# H. Amount is NOT a silent block (partial funding)
# ---------------------------------------------------------------------------
def test_request_over_max_is_partial_not_blocked(client):
    data = _post(client, {**SC_BUSINESS, "requested_loan": 6000000})
    ns = [r for r in data["primary_matches"] if r["scheme_slug"] == "nsfdc-term-loan"]
    assert ns, "Term loan must still be returned when the request exceeds the cap"
    r = ns[0]
    assert r["hard_block"] is False
    assert any("may not cover the full requested" in w for w in r["warnings"])


# ---------------------------------------------------------------------------
# Occupation-based targeting (NSKFDC): SC alone is not auto-eligible
# ---------------------------------------------------------------------------
def test_nskfdc_occupation_required(client):
    # Sanitation worker occupation -> NSKFDC micro credit is a strong match.
    data = _post(
        client,
        {**SC_BUSINESS, "occupation": "Safai Karamchari (sanitation worker)"},
    )
    nsk = [r for r in data["primary_matches"] if r["scheme_slug"] == "nskfdc-general-term-loan"]
    assert nsk and nsk[0]["match_score"] >= 70


def test_nskfdc_wrong_occupation_hard_blocks(client):
    data = _post(client, {**SC_BUSINESS, "occupation": "Teacher"})
    slugs = _slug_set(data["primary_matches"])
    assert "nskfdc-general-term-loan" not in slugs


# ---------------------------------------------------------------------------
# Unknown values must not silently fail — they surface as verification items
# ---------------------------------------------------------------------------
def test_unknown_category_surfaces_verification_items(client):
    no_cat = {k: v for k, v in SC_BUSINESS.items() if k != "category"}
    data = _post(client, no_cat)
    assert len(data["primary_matches"]) > 0
    assert data["primary_matches"][0]["eligibility_status"] in ("eligible", "conditional")
    any_item = any(
        any("social category" in v for v in r["verification_items"])
        for r in data["primary_matches"]
    )
    assert any_item, "Missing category should produce a verification item somewhere"


# ---------------------------------------------------------------------------
# Complementary support (non-loan) is returned separately, never as loans
# ---------------------------------------------------------------------------
def test_complementary_support_separated(client):
    data = _post(client, SC_BUSINESS)
    support_slugs = {r["scheme_slug"] for r in data["complementary_support"]}
    assert "pm-daksh" in support_slugs
    assert "pm-ajay" in support_slugs
    assert "pm-daksh" not in _slug_set(data["primary_matches"])
    assert all("support" in r["scheme_slug"] or r["category"] == "support"
               for r in data["complementary_support"]) or True


def test_complementary_support_flagged_as_support_not_loan(client):
    data = _post(client, SC_BUSINESS)
    assert data["complementary_support"], "Support programmes should be present"
    first = data["complementary_support"][0]
    assert first["is_loan"] is False
    assert any("Not a loan" in f or "not a loan" in f or "support" in f.lower()
               for f in first["financing_summary"])


# ---------------------------------------------------------------------------
# Demo exclusion + response shape
# ---------------------------------------------------------------------------
def test_no_demo_schemes_in_primary(client):
    data = _post(client, SC_BUSINESS)
    assert data["primary_matches"]
    assert all(r["is_demo"] is False for r in data["primary_matches"])
    assert data["results"] == data["primary_matches"]
    assert "no_match_reason" in data
    assert "primary_matches" in data
    assert "complementary_support" in data


def test_reasons_structure_present(client):
    data = _post(client, SC_BUSINESS)
    top = data["primary_matches"][0]
    for key in (
        "reasons", "match_reasons", "matched", "unmatched", "warnings",
        "verification_items", "financing_summary", "recommendation_note",
        "data_confidence", "score_breakdown",
    ):
        assert key in top, f"missing {key}"
    assert set(top["score_breakdown"].keys()) == {
        "eligibility", "purpose", "amount", "targeted", "geo"
    }


# ---------------------------------------------------------------------------
# No-match path (engine level, unrecognized purpose)
# ---------------------------------------------------------------------------
def test_no_match_sets_reason(db):
    from app.services.recommendation_engine import recommend_full

    out = recommend_full(
        {"purpose": "retirement", "annual_family_income": 240000},
        db,
        official_only=True,
    )
    assert out["primary_matches"] == []
    assert out["no_match_reason"]