"""
Part 4 official-source data-integrity tests.

Covers the official-source cleanup that was completed against the live
government pages (2026-09-11):

- every active public scheme is an official, non-demo government record;
- confidence is never more optimistic than the source (verified vs needs_review);
- support programmes (PM-DAKSH/PM-AJAY) are never returned as loans;
- official scheme URLs are government domains only (no third-party sources);
- NBCFDC records match the official Individual Loan Scheme / Pattern of
  Finance figures (income Rs 5L, max Rs 25L, education at 8%, 85/15 finance);
- unconfirmed fields stay null/unknown instead of leaking as invented values.

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
from app.models import Scheme
from app.services.scheme_import import import_official_schemes

OFFICIAL_DOMAINS = (
    "nsfdc.nic.in",
    "nbcfdc.gov.in",
    "nskfdc.nic.in",
    "myscheme.gov.in",
    "socialjustice.gov.in",
)


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    try:
        seed(s)
        import_official_schemes(s)
    finally:
        pass
    yield s
    s.close()


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db_ = SessionLocal()
    try:
        seed(db_)
    finally:
        db_.close()
    with TestClient(app) as c:
        yield c


def _active_official(schemes):
    return [
        s
        for s in schemes
        if s.active and s.is_demo is False and s.official is True
    ]


def _rules_profile():
    return {
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


# ---------------------------------------------------------------------------
# Every active public scheme is official + metadata present (spec §3/§7)
# ---------------------------------------------------------------------------
def test_all_active_schemes_are_official(db):
    official = _active_official(db.query(Scheme).all())
    assert len(official) == 20, "expected exactly 20 active official records"
    for s in official:
        assert s.source_type == "official_government"
        assert s.data_confidence in ("verified", "needs_review")
        assert s.verification_status in ("verified", "needs_review")
        assert s.last_verified, f"{s.slug} missing last_verified"
        assert s.official_scheme_url, f"{s.slug} missing official_scheme_url"
        assert s.official_scheme_url.startswith("https://")
        assert any(d in s.official_scheme_url for d in OFFICIAL_DOMAINS), (
            f"{s.slug} uses a non-official source URL: {s.official_scheme_url}"
        )


def test_no_active_demo_schemes(db):
    assert not [s for s in db.query(Scheme).all() if s.active and s.is_demo]


def test_no_duplicate_names_or_slugs(db):
    schemes = db.query(Scheme).all()
    names = [s.name for s in schemes]
    slugs = [s.slug for s in schemes]
    assert len(names) == len(set(names))
    assert len(slugs) == len(set(slugs))


# ---------------------------------------------------------------------------
# Verification outcome is stable and never over-claims (spec §2/§5)
# ---------------------------------------------------------------------------
def test_verification_counts_per_provider(db):
    official = _active_official(db.query(Scheme).all())
    by_provider = {}
    for s in official:
        by_provider.setdefault(s.provider, []).append(s.data_confidence)
    assert by_provider["NSFDC"] == ["verified"] * 5
    assert by_provider["NBCFDC"].count("verified") == 2
    assert by_provider["NBCFDC"].count("needs_review") == 2
    assert by_provider["NSKFDC"] == ["needs_review"] * 9
    assert len(by_provider["DOSJE"]) == 2
    assert db.query(Scheme).filter(Scheme.slug.in_(["pm-daksh", "pm-ajay"])).count() == 2


def test_nskfdc_eligibility_stays_occupation_based(db):
    nsk = db.query(Scheme).filter(Scheme.provider == "NSKFDC").all()
    assert nsk
    for s in nsk:
        assert s.occupation_groups, f"{s.slug} lost occupation targeting"
        assert "Safai Karamcharis" in " | ".join(s.occupation_groups)


# ---------------------------------------------------------------------------
# NBCFDC values match the official pages (spec §3)
# ---------------------------------------------------------------------------
def test_nbcfdc_general_loan_official_values(db):
    s = db.query(Scheme).filter(Scheme.slug == "nbcfdc-general-loan").first()
    assert s.verification_status == "verified"
    assert s.income_limit == 500000
    assert s.max_loan_amount == 2500000
    assert s.max_loan == 2500000
    assert s.interest_rate == 8.0
    assert s.interest_rate_type == "tiered"
    assert s.interest_tiers == [
        {"loan_up_to": 125000, "interest_rate": 7.0},
        {"loan_up_to": 2500000, "interest_rate": 8.0},
    ]
    assert s.finance_percentage == 85.0
    assert s.tenure_months == 84
    assert s.moratorium_months == 3


def test_nbcfdc_education_loan_official_values(db):
    s = db.query(Scheme).filter(Scheme.slug == "nbcfdc-education-loan").first()
    assert s.verification_status == "verified"
    assert s.income_limit == 500000
    assert s.max_loan_amount == 2500000
    assert s.max_loan == 2500000
    assert s.interest_rate == 8.0
    assert s.interest_rate_type == "fixed"
    assert s.finance_percentage == 85.0
    assert s.tenure_months == 120
    assert s.moratorium_months == 60
    assert "50% marks" in (s.education_requirements or "")


def test_stale_nbcfdc_figures_are_gone(db):
    rows = db.query(Scheme).filter(Scheme.provider == "NBCFDC").all()
    assert all((s.income_limit or 0) != 300000 for s in rows), "stale Rs 3L ceiling"
    edu = db.query(Scheme).filter(Scheme.slug == "nbcfdc-education-loan").first()
    assert edu.interest_rate != 4.0, "stale 4% education rate"


# ---------------------------------------------------------------------------
# Unconfirmed fields stay unknown — never invented (spec §4/§5)
# ---------------------------------------------------------------------------
def test_unconfirmed_income_stays_null(db):
    for slug in ("nbcfdc-new-swarnima-women", "nbcfdc-mahila-samriddhi"):
        s = db.query(Scheme).filter(Scheme.slug == slug).first()
        assert s.data_confidence == "needs_review"
        assert s.income_limit is None, f"{slug} income_limit must stay unknown"
        assert s.income_threshold is None, f"{slug} income_threshold must stay unknown"


def test_tiered_rate_unknown_stays_null(db):
    s = db.query(Scheme).filter(Scheme.slug == "nsfdc-udyam-nidhi").first()
    assert s.data_confidence == "verified"
    assert s.interest_rate is None, "tiered scheme must not coerce a flat rate"
    assert s.interest_rate_type == "tiered"
    assert s.interest_tiers


def test_project_cost_unknown_for_nbcfdc_general(db):
    s = db.query(Scheme).filter(Scheme.slug == "nbcfdc-general-loan").first()
    assert s.project_min is None
    assert s.project_max is None
    assert s.project_cost_min is None
    assert s.project_cost_max is None


# ---------------------------------------------------------------------------
# Support programmes are not loans (spec §4 — PM-DAKSH / PM-AJAY)
# ---------------------------------------------------------------------------
def test_support_schemes_flagged_not_loan(db):
    for slug in ("pm-daksh", "pm-ajay"):
        s = db.query(Scheme).filter(Scheme.slug == slug).first()
        assert s.is_loan is False
        assert s.category == "support"
        assert s.verification_status == "verified"
    loans = db.query(Scheme).filter(Scheme.active.is_(True), Scheme.is_loan.is_(True)).all()
    assert all(l.category != "support" for l in loans)


def test_loan_schemes_are_loans(db):
    non_support = [
        s
        for s in _active_official(db.query(Scheme).all())
        if s.category != "support"
    ]
    assert non_support
    assert all(s.is_loan for s in non_support)


def test_support_not_recommended_as_loans(client):
    r = client.post("/api/recommendations", json={"profile": _rules_profile()})
    assert r.status_code == 200
    data = r.json()
    primary = data["primary_matches"]
    assert primary
    assert all(p["is_loan"] is True for p in primary), "loans section must not contain support"
    support_slugs = {s["scheme_slug"] for s in data["complementary_support"]}
    assert "pm-daksh" in support_slugs
    assert "pm-ajay" in support_slugs


# ---------------------------------------------------------------------------
# needs_review is preserved end-to-end (spec §5/§9 — no false "Verified" claims)
# ---------------------------------------------------------------------------
def test_needs_review_preserved_in_api_results(client):
    profile = {
        **_rules_profile(),
        "occupation": "Safai Karamchari (sanitation worker)",
    }
    r = client.post("/api/recommendations", json={"profile": profile})
    assert r.status_code == 200
    matches = {m["scheme_slug"]: m for m in r.json()["primary_matches"]}
    nsk = matches.get("nskfdc-general-term-loan")
    assert nsk, "NSKFDC term loan should match a sanitation-worker profile"
    assert nsk["data_confidence"] == "needs_review"
    assert nsk["verification_status"] == "needs_review"
    assert any("review" in (m["data_confidence"] or "") for m in r.json()["primary_matches"])


def test_verified_records_expose_verified_confidence(client):
    r = client.post("/api/recommendations", json={"profile": _rules_profile()})
    data = r.json()
    nsfdc = [m for m in data["primary_matches"] if m["scheme_slug"].startswith("nsfdc-")]
    assert nsfdc
    assert all(m["data_confidence"] == "verified" for m in nsfdc)


# ---------------------------------------------------------------------------
# API serializes the official-source metadata (spec §9)
# ---------------------------------------------------------------------------
def test_schemes_api_exposes_metadata_without_zeroing(client):
    r = client.get("/api/schemes")
    assert r.status_code == 200
    by_slug = {s["slug"]: s for s in r.json()}
    sw = by_slug["nbcfdc-new-swarnima-women"]
    assert sw["data_confidence"] == "needs_review"
    assert sw["income_limit"] is None, "unconfirmed income must not become 0"
    udyam = by_slug["nsfdc-udyam-nidhi"]
    assert udyam["interest_rate"] is None
    gen = by_slug["nbcfdc-general-loan"]
    assert gen["income_limit"] == 500000
    assert gen["data_confidence"] == "verified"
    for slug in ("pm-daksh", "pm-ajay"):
        assert by_slug[slug]["is_loan"] is False
        assert by_slug[slug]["official_scheme_url"].startswith(
            "https://www.myscheme.gov.in/schemes/"
        )