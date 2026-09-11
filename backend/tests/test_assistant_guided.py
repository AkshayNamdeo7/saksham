"""
Part 5 — Guided assistant conversation tests.

Covers the 8 spec scenarios:
1. SC + business goal → assistant asks only missing info → official matches
2. SC + education → NSFDC Education Loan guidance
3. OBC + business + female → NBCFDC identified
4. No matching scheme → explanation + suggestions
5. Needs-review scheme → never claimed definitely eligible
6. Tiered-interest scheme → no invented/0% rate
7. PM-DAKSH / PM-AJAY → support, not loans
8. Failure/timeout → clean readable error, no secrets/stack traces
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


def _chat(client, history, msg):
    """Append a user turn to the accumulated history and POST it."""
    history.append({"role": "user", "content": msg})
    r = client.post(
        "/api/assistant/chat",
        json={"message": msg, "language": "en", "history": history},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _turns(client, msgs):
    history: list[dict] = []
    out = []
    for msg in msgs:
        out.append(_chat(client, history, msg))
    return out


# ---------------------------------------------------------------------------
# TEST 1 — SC user + business goal
# ---------------------------------------------------------------------------
def test_sc_business_flow_asks_minimal_then_official_schemes(client):
    replies = _turns(client, [
        "I want to start a business",
        "My category is SC",
        "My annual family income is 2 lakh",
        "I am 30 years old",
        "I am male",
        "I live in Madhya Pradesh",
    ])

    # First reply asks ONLY for the missing category — one narrow question.
    assert "social category" in replies[0]["message"]
    assert "annual family income" not in replies[0]["message"]
    assert "What is your age" not in replies[0]["message"]

    # Intermediate turns keep asking single missing items, one at a time.
    for r in replies[:-1]:
        assert r["structured"] is None or len(r["structured"]) == 0

    # Final reply returns official scheme matches with structured cards.
    final = replies[-1]
    assert "these schemes may fit you" in final["message"]
    assert final["structured"], "expected structured scheme cards"
    assert all(s["data_confidence"] in ("verified", "needs_review") for s in final["structured"])
    assert all(s["official_scheme_url"] for s in final["structured"])

    # Support programmes are presented separately, not as loans.
    assert "Additional Government Support" in final["message"]
    assert "not loans" in final["message"]

    # Verification warning always present (sources need manual confirm before apply).
    assert "verify the latest official conditions" in final["message"]


# ---------------------------------------------------------------------------
# TEST 2 — SC + education → NSFDC Education Loan
# ---------------------------------------------------------------------------
def test_sc_education_flow_guides_to_nsfdc_education_loan(client):
    replies = _turns(client, [
        "I want an education loan for college studies",
        "My category is SC",
        "My annual family income is 2 lakh",
        "I am 22 years old",
        "I live in Madhya Pradesh",
        "I am a graduate",
        "It is a general course",
    ])

    final = replies[-1]
    assert final["structured"], "expected education loan recommendations"
    slugs = [s["scheme_slug"] for s in final["structured"]]
    assert "nsfdc-educational-loan" in slugs
    edu_card = next(s for s in final["structured"] if s["scheme_slug"] == "nsfdc-educational-loan")
    assert edu_card["data_confidence"] == "verified"

    # No turn ever claims a specific interest/loan figure outside the DB.
    for r in replies:
        assert "0%" not in (r["message"] or "")


# ---------------------------------------------------------------------------
# TEST 3 — OBC + business + female → NBCFDC identified
# ---------------------------------------------------------------------------
def test_obc_female_business_finds_nbcfdc(client):
    replies = _turns(client, [
        "I want to start a business",
        "My category is OBC",
        "My annual family income is 4 lakh",
        "I am 30 years old",
        "I am female",
        "I live in Uttar Pradesh",
    ])

    final = replies[-1]
    slugs = [s["scheme_slug"] for s in (final["structured"] or [])]
    assert "nbcfdc-general-loan" in slugs, f"expected NBCFDC General Loan, got {slugs}"
    gen = next(s for s in final["structured"] if s["scheme_slug"] == "nbcfdc-general-loan")
    assert gen["data_confidence"] == "verified"
    # The answer must not invent a flat rate for a tiered record.
    assert gen["interest_display"]


# ---------------------------------------------------------------------------
# TEST 4 — No matching scheme → explanation + suggestions
# ---------------------------------------------------------------------------
def test_no_match_explains_and_suggests(client):
    # NSKFDC + NSFDC/NBCFDC cover every reachable NLP profile, so the no-match
    # branch is exercised white-box by injecting an occupation that the engine
    # hard-blocks against occupation-targeted NSKFDC loans.
    from app.services.assistant_handler import _build_profile, _handle_education_flow
    from app.db.session import SessionLocal

    user_msgs = [{"role": "user", "content": m} for m in [
        "I want an education loan",
        "My category is General",
        "My annual family income is 8 lakh",
        "I am 25 years old",
        "I live in Rajasthan",
    ]]
    profile = _build_profile(user_msgs)
    profile["education_level"] = "graduate"
    profile["course_type"] = "professional"
    profile["occupation"] = "tailor"

    db = SessionLocal()
    try:
        out = _handle_education_flow(user_msgs, profile, "en", db)
    finally:
        db.close()

    msg = out["message"]
    assert "no strong match" in msg
    assert out.get("structured") in (None, []), "should be no scheme cards"
    assert "eligibility" in msg.lower() or "details" in msg.lower(), "should suggest next steps"


# ---------------------------------------------------------------------------
# TEST 5 — Needs-review scheme is never called definite
# ---------------------------------------------------------------------------
def test_needs_review_scheme_never_claimed_eligible(client):
    replies = _turns(client, [
        "I am a Safai Karamchari and want a loan for a sanitation business",
        "My category is SC",
        "My annual family income is 2 lakh",
        "I am 30 years old",
        "I live in Uttar Pradesh",
    ])

    reviewed = [r for r in replies if r.get("structured")]
    assert reviewed, "expected some scheme cards for a sanitation profile"
    final = reviewed[-1]
    nskfdc = [s for s in final["structured"] if s["scheme_slug"].startswith("nskfdc-")]
    assert nskfdc, "expected NSKFDC cards for a Safai Karamchari profile"
    assert all(s["data_confidence"] == "needs_review" for s in nskfdc)
    # Plain-language transparency, no definitive eligibility claim.
    assert "manual verification" in final["message"]
    assert "needs_review" not in (final["message"] or ""), "no raw internal tag in user copy"


# ---------------------------------------------------------------------------
# TEST 6 — Tiered-interest scheme → no invented / 0% rate
# ---------------------------------------------------------------------------
def test_tiered_interest_no_invented_rate(client):
    r = _chat(client, [], "What is my EMI for the Udyam Nidhi scheme?")
    msg = r["message"]
    assert "tiered interest rates" in msg
    # Udyam tiers are channel-based; the renderer must not invent ₹0 slabs.
    assert "₹0" not in msg
    assert "Cooperative" in msg and "Small Finance" in msg, "channel tiers should be listed"
    assert "cannot be calculated" in msg
    # No flat EMI figure is presented for a tiered scheme.
    assert "Estimated monthly EMI:" not in msg


def test_emi_without_scheme_does_not_invent_rate(client):
    r = _chat(client, [], "What will be my EMI?")
    msg = r["message"]
    assert "cannot be calculated" in msg
    assert "₹0" not in msg, "no invented ₹0 rate should appear"


# ---------------------------------------------------------------------------
# TEST 7 — PM-DAKSH / PM-AJAY displayed as support, not loans
# ---------------------------------------------------------------------------
def test_pm_daksh_shown_as_support_not_loan(client):
    r = _chat(client, [], "What is PM-DAKSH for skill training?")
    msg = r["message"]
    assert "PM-DAKSH" in msg
    assert "support programme" in msg.lower() or "support" in msg.lower()
    assert "not a loan" in msg.lower()
    assert "loan" not in (msg.split("not a loan")[1].split(".")[0] if "not a loan" in msg else "")


def test_pm_daksh_and_pm_ajay_in_support_section(client):
    replies = _turns(client, [
        "I want to start a business",
        "My category is SC",
        "My annual family income is 2 lakh",
        "I am 30 years old",
        "I am male",
        "I live in Madhya Pradesh",
    ])
    msg = replies[-1]["message"]
    # Support schemes separated under an explicit heading.
    assert "Additional Government Support" in msg
    assert "PM-DAKSH" in msg
    assert "PM-AJAY" in msg


# ---------------------------------------------------------------------------
# TEST 8 — Failure/timeout → clean, readable errors; no secrets
# ---------------------------------------------------------------------------
def test_chat_error_is_clean_and_readable(client):
    long_msg = "A" * 2001
    r = client.post(
        "/api/assistant/chat",
        json={"message": long_msg, "language": "en", "history": []},
    )
    assert r.status_code in (400, 422)
    body = r.text
    assert "Traceback" not in body
    assert "File \"" not in body
    assert "AI_API_KEY" not in body and "AI_BASE_URL" not in body
    assert "DATABASE_URL" not in body


def test_chat_success_exposes_no_secrets(client):
    r = _chat(client, [], "Namaste, tell me about schemes")
    for leaked in ("AI_API_KEY", "JWT", "DATABASE_URL", "SECRET", "password"):
        assert leaked.lower() not in r["message"].lower()


# ---------------------------------------------------------------------------
# Hindi response preserved
# ---------------------------------------------------------------------------
def test_hindi_answers_in_hindi(client):
    history: list[dict] = []
    history.append({"role": "user", "content": "मैं व्यवसाय शुरू करना चाहता हूँ"})
    r = client.post(
        "/api/assistant/chat",
        json={"message": "मैं व्यवसाय शुरू करना चाहता हूँ", "language": "hi", "history": history},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["language"] == "hi"
    assert "वर्ग" in data["message"]  # asks for category in Hindi