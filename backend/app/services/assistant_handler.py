"""
Intent-based assistant handler.

The assistant extracts structured signals from free text and delegates to the
deterministic services (recommendation engine, calculator, partner routing,
document checklist). It only uses AI for a final natural-language wrap where an
API key is configured; otherwise it returns deterministic template responses.
"""

import json

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Scheme
from app.services.ai_service import (
    ai_service,
    extract_profile_from_text,
)
from app.services.calculator import calculate_loan
from app.services.partner_routing import route_partners
from app.services.recommendation_engine import recommend

SUGGESTIONS = [
    {"key": "scheme", "en": "Which scheme may suit me?", "hi": "कौन सी योजना मेरे लिए उपयुक्त हो सकती है?"},
    {"key": "documents", "en": "What documents might I need?", "hi": "मुझे कौन से दस्तावेज़ चाहिए?"},
    {"key": "emi", "en": "How can I estimate my EMI?", "hi": "मैं अपनी EMI का अनुमान कैसे लगाऊं?"},
    {"key": "partner", "en": "How do I find a channel partner?", "hi": "मुझे चैनल पार्टनर कैसे मिलेगा?"},
    {"key": "why", "en": "Why was this scheme recommended?", "hi": "यह योजना क्यों अनुशंसित की गई?"},
]

def handle_conversation(messages: list[dict], language: str = "en") -> dict:
    user_msgs = [m for m in messages if m.get("role") == "user"]
    last = dict(user_msgs[-1]) if user_msgs else {}
    text = (last.get("content") or "").strip()

    intent = _detect_intent(text.lower())
    extracted = extract_profile_from_text(text)

    db = SessionLocal()
    try:
        if intent == "emi":
            return _respond_emi(text, extracted, language)
        if intent in ("partner", "partner_route"):
            return _respond_partner(text, extracted, language)
        if intent == "documents":
            return _respond_documents(text, extracted, language)
        if intent == "why":
            return _respond_why(text, extracted, language)
        if intent == "scheme" or extracted.get("purpose") or extracted.get("requested_loan"):
            return _respond_scheme(text, extracted, language)
        return _respond_general(text, extracted, language)
    finally:
        db.close()


def _detect_intent(text: str) -> str:
    emi = ["emi", "installment", "ekmisi", "किस्त", "interest"]
    partner = ["partner", "channel partner", "nearby", "bank", "branch", "पार्टनर", "चैनल", "बैंक", "location"]
    docs = ["document", "कागज", "दस्तावेज़", "documentation"]
    why = ["why", "recommended", "क्यों", "सिफारिश", "matches"]
    scheme_intent = ["which scheme", "कौन सी योजना", "scheme", "योजना", "loan", "लोन", "loan chahiye", "चाहिए"]
    for kw in emi:
        if kw in text:
            return "emi"
    for kw in docs:
        if kw in text:
            return "documents"
    for kw in why:
        if kw in text:
            return "why"
    for kw in partner:
        if kw in text:
            return "partner"
    for kw in scheme_intent:
        if kw in text:
            return "scheme"
    return "general"


def _respond_scheme(text, extracted, language):
    purpose = extracted.get("purpose")
    loan = extracted.get("requested_loan")
    project_cost = extracted.get("project_cost")
    profile = {
        "purpose": purpose or "business",
        "project_cost": project_cost,
        "requested_loan": loan,
        "annual_family_income": 240000,
    }
    results = recommend(profile, db)
    eligible = [r for r in results if r["eligibility_status"] in ("eligible", "conditional")][:3]

    if not eligible:
        return _reply(
            language,
            en="I couldn't find a very strong match yet. Could you share your purpose and approximate project cost?",
            hi="मुझे अभी कोई बहुत मजबूत मिलान नहीं मिला। क्या आप अपना उद्देश्य और अनुमानित परियोजना लागत बता सकते हैं?",
        )

    top = eligible[0]
    scheme = _scheme_name(top, language)
    scheme_row = db.query(Scheme).filter(Scheme.id == top["scheme_id"]).first()
    demo_limit = getattr(scheme_row, "max_loan", 0) if scheme_row else 0
    top_text = (
        f"I reviewed your requirements. A strong match is **{scheme['name']}** "
        f"(demo match score {top['match_score']}%).\n\n"
        f"Best-fit demo limit: ₹{demo_limit:,.0f}.\n\n"
        "You can calculate your EMI, compare schemes, or find a channel partner next."
        if language == "en"
        else f"मैंने आपकी आवश्यकताओं की समीक्षा की। एक मजबूत मिलान **{scheme['name']}** है (डेमो मैच स्कोर {top['match_score']}%)।\n\nडेमो अधिकतम सीमा: ₹{demo_limit:,.0f}।\n\nआप EMI की गणना, योजनाओं की तुलना, या चैनल पार्टनर खोज सकते हैं।"
    )
    if ai_service.enabled:
        ai_text = ai_service.assistant_reply(
            [{"role": "user", "content": text}], language
        )
        if ai_text:
            return _reply(language, en=ai_text, hi=ai_text)
    return _reply(language, en=top_text, hi=top_text)


def _respond_emi(text, extracted, language):
    loan = extracted.get("requested_loan") or 100000
    if loan > 2000000:
        loan = 2000000
    calc = calculate_loan(loan, 4.0, 36, "months", 0)
    vals = {
        "principal": loan,
        "emi": calc["emi"],
        "": 0,
    }
    en = (
        f"For a demo loan of ₹{loan:,.0f} over 3 years at an indicative 4% p.a., "
        f"your estimated EMI would be **₹{calc['emi']:,.2f}** per month.\n\n"
        f"Total interest (demo): ₹{calc['total_interest']:,.2f}. "
        "Actual figures depend on the final scheme terms."
    )
    hi = (
        f"डेमो ऋण ₹{loan:,.0f} के लिए 3 वर्ष में संकेतिक 4% वार्षिक दर पर, "
        f"आपकी अनुमानित किस्त **₹{calc['emi']:,.2f}** प्रति माह होगी।\n\n"
        f"कुल ब्याज (डेमो): ₹{calc['total_interest']:,.2f}। वास्तविक राशि अंतिम योजना शर्तों पर निर्भर करती है।"
    )
    return _reply(language, en, hi)


def _respond_partner(text, extracted, language):
    scored = route_partners({"scheme_id": None, "purpose": "business"}, db)
    if not scored:
        return _reply(language, en="No demo partners available right now.", hi="अभी कोई डेमो पार्टनर उपलब्ध नहीं है।")
    top = scored[0]["partner"]
    en = (
        f"A strong demo match is **{top.name}** ({top.type}) in {top.city}, {top.state}. "
        f"Demo routing score {(scored[0]['total'])}/100.\n\n"
        "Contact: " + top.phone + ". This is prototype partner data."
    )
    hi = (
        f"एक मजबूत डेमो मिलान **{top.name}** ({top.type}), {top.city}, {top.state} है। "
        f"डेमो रूटिंग स्कोर {scored[0]['total']}/100।\n\nसंपर्क: {top.phone}। यह प्रोटोटाइप पार्टनर डेटा है।"
    )
    return _reply(language, en, hi)


def _respond_documents(text, extracted, language):
    en = (
        "Typically you may need (demo):\n"
        "• Aadhaar / identity proof\n"
        "• Caste certificate\n"
        "• Income certificate\n"
        "• Bank account details\n"
        "• Project report (business) or admission proof (education)\n\n"
        "The exact set depends on the scheme. Check the Scheme Details page for the scheme-specific checklist."
    )
    hi = (
        "आमतौर पर ये दस्तावेज़ लग सकते हैं (डेमो):\n"
        "• आधार / पहचान प्रमाण\n"
        "• जाति प्रमाण पत्र\n"
        "• आय प्रमाण पत्र\n"
        "• बैंक खाता विवरण\n"
        "• परियोजना रिपोर्ट (व्यवसाय) या प्रवेश प्रमाण (शिक्षा)\n\n"
        "सटीक सूची योजना पर निर्भर करती है। योजना विवरण पृष्ठ पर योजना-विशिष्ट सूची देखें।"
    )
    return _reply(language, en, hi)


def _respond_why(text, extracted, language):
    purpose = extracted.get("purpose") or "business"
    results = recommend({"purpose": purpose, "project_cost": extracted.get("project_cost")}, db)
    if not results:
        return _reply(language, en="No recommendation available to explain yet.", hi="अभी समझाने के लिए कोई अनुशंसा उपलब्ध नहीं है।")
    top = results[0]
    scheme = _scheme_name(top, language)
    reasons = "\n".join(f"• {r}" for r in top["reasons"][:3])
    en = (
        f"**{scheme['name']}** was recommended because:\n{reasons}\n\n"
        f"Match score: {top['match_score']}% (status: {top['eligibility_status']}). This is a demo assessment."
    )
    hi = (
        f"**{scheme['name']}** निम्न कारणों से अनुशंसित था:\n{reasons}\n\n"
        f"मैच स्कोर: {top['match_score']}% (स्थिति: {top['eligibility_status']})। यह एक डेमो मूल्यांकन है।"
    )
    return _reply(language, en, hi)


def _respond_general(text, extracted, language):
    if extracted.get("purpose") or extracted.get("requested_loan"):
        return _respond_scheme(text, extracted, language)
    en = (
        "I can help you with:\n"
        "• Which scheme may suit you\n"
        "• Document requirements\n"
        "• EMI estimates\n"
        "• Channel partner discovery\n\n"
        "Try: 'Mujhe ₹1 lakh ki dairy business ke liye loan chahiye'"
    )
    hi = (
        "मैं इसमें मदद कर सकता हूँ:\n"
        "• कौन सी योजना आपके लिए उपयुक्त है\n"
        "• दस्तावेज़ आवश्यकताएँ\n"
        "• EMI अनुमान\n"
        "• चैनल पार्टनर खोज\n\n"
        "आज़माएँ: 'Mujhe ₹1 lakh ki dairy business ke liye loan chahiye'"
    )
    return _reply(language, en, hi)


def _scheme_name(result, language):
    name = result.get("scheme_name") or "Recommended scheme"
    return {"name": name}


def _reply(language, en, hi):
    text = hi if language == "hi" else en
    return {
        "message": text,
        "language": language,
        "suggestions": SUGGESTIONS,
        "structured": None,
    }