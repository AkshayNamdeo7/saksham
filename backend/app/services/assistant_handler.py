"""
Guided conversation assistant for Saksham.

Stateless design: the full message history is sent with every request.
The handler reconstructs conversation state from history, extracts profile
fields from all user messages, determines what to ask next or what to
show, and returns a structured response.

Core principle: financial and eligibility facts come from the official
scheme database via the recommendation engine.  The assistant NEVER
invents loan amounts, interest rates, eligibility, documents, or
approval probability.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Scheme
from app.services.ai_service import ai_service, extract_profile_from_text
from app.services.calculator import calculate_loan
from app.services.partner_routing import route_partners
from app.services.recommendation_engine import recommend_full

# ---------------------------------------------------------------------------
# Suggestion chips shown in the frontend
# ---------------------------------------------------------------------------
SUGGESTIONS = [
    {"key": "scheme", "en": "Which scheme may suit me?", "hi": "कौन सी योजना मेरे लिए उपयुक्त हो सकती है?"},
    {"key": "documents", "en": "What documents might I need?", "hi": "मुझे कौन से दस्तावेज़ चाहिए?"},
    {"key": "emi", "en": "How can I estimate my EMI?", "hi": "मैं अपनी EMI का अनुमान कैसे लगाऊं?"},
    {"key": "partner", "en": "How do I find a channel partner?", "hi": "मुझे चैनल पार्टनर कैसे मिलेगा?"},
    {"key": "why", "en": "Why was this scheme recommended?", "hi": "यह योजना क्यों अनुशंसित की गई?"},
]

# ---------------------------------------------------------------------------
# Goal keywords
# ---------------------------------------------------------------------------
_GOAL_BUSINESS_NEW = [
    "start a business", "new business", "shuru karna", "शुरू करना",
    "business karna", "व्यवसाय", "start business", "नया व्यवसाय",
    "dairy", "डेयरी", "shop", "दुकान", "manufactur", "निर्माण",
    "trade", "retail",
]
_GOAL_BUSINESS_EXISTING = [
    "existing business", "expand", "विस्तार", "growth", "बढ़ाना",
    "already have", "पहले से", "upgrade", "equipment", "उपकरण",
]
_GOAL_EDUCATION = [
    "education", "शिक्षा", "study", "पढ़ाई", "course", "कोर्स",
    "college", "कॉलेज", "university", "विश्वविद्यालय", "degree",
    "diploma", "b.ed", "btech", "mbbs", "llb", "coaching",
    "tuition", "admission", "प्रवेश", "fee", "फीस",
]
_GOAL_SANITATION = [
    "sanitation", "स्वच्छता", "safai", "सफाई", "toilet", "शौचालय",
    "waste", "कचरा", "clean", "स्वच्छ",
]
_GOAL_SKILL = [
    "skill", "कौशल", "training", "प्रशिक्षण", "pm-daksh", "pm daksh",
    "vocational", "प्राविधिक",
]

# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------
_CATEGORY_MAP = {
    "sc": "SC", "st": "ST", "obc": "OBC", "ebc": "EBC",
    "general": "General", "gen": "General",
    "s.c.": "SC", "s.t.": "ST", "o.b.c.": "OBC", "e.b.c.": "EBC",
    "अनुसूचित जाति": "SC", "अनुसूचित जनजाति": "ST",
    "अन्य पिछड़ा वर्ग": "OBC", "सामान्य": "General",
}

# Indian states for detection
_INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand",
    "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
    "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
    "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
    "uttar pradesh", "uttarakhand", "west bengal",
    "delhi", "chandigarh", "jammu", "kashmir", "ladakh",
    "andaman", "lakshadweep", "puducherry", "dadra",
    # Hindi
    "मध्य प्रदेश", "उत्तर प्रदेश", "महाराष्ट्र", "राजस्थान",
    "गुजरात", "बिहार", "तमिल नाडु", "कर्नाटक", "पश्चिम बंगाल",
    "आंध्र प्रदेश", "तेलंगाना", "केरल", "ओडिशा", "छत्तीसगढ़",
    "झारखंड", "उत्तराखंड", "हिमाचल प्रदेश", "पंजाब", "हरियाणा",
    "दिल्ली", "जम्मू", "कश्मीर",
]


# ===================================================================
# Public entry point
# ===================================================================

def handle_conversation(messages: list[dict], language: str = "en") -> dict:
    """Main entry point called by the /api/assistant/chat route."""
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return _reply(language, _greeting_en(), _greeting_hi())

    last_text = (user_msgs[-1].get("content") or "").strip()
    lower = last_text.lower()

    # 1. Reconstruct conversation state from ALL user messages
    profile = _build_profile(user_msgs)
    goal = _detect_goal(lower, profile)

    # 2. Check for special intents first
    intent = _detect_intent(lower)

    # 3. Dispatch
    db = SessionLocal()
    try:
        if intent == "emi":
            return _handle_emi(last_text, profile, language, db)
        if intent == "documents":
            return _handle_documents(profile, language, db)
        if intent == "partner":
            return _handle_partner(profile, language, db)
        if intent == "why":
            return _handle_why(profile, language, db)

        # Goal-based guided flow
        if goal == "education":
            return _handle_education_flow(user_msgs, profile, language, db)
        if goal == "sanitation":
            return _handle_sanitation_flow(profile, language, db)
        if goal == "skill":
            return _handle_skill_flow(profile, language, db)
        if goal in ("business_new", "business_existing"):
            return _handle_business_flow(user_msgs, profile, goal, language, db)

        # Default: guided flow based on what we know
        return _handle_guided_flow(user_msgs, profile, language, db)
    finally:
        db.close()


# ===================================================================
# Profile building from conversation history
# ===================================================================

def _build_profile(user_msgs: list[dict]) -> dict:
    """Extract all profile fields mentioned across ALL user messages."""
    profile: dict = {}
    for m in user_msgs:
        text = (m.get("content") or "").strip()
        lower = text.lower()

        # Amount extraction
        extracted = extract_profile_from_text(text)
        if extracted.get("requested_loan") and "requested_loan" not in profile:
            profile["requested_loan"] = extracted["requested_loan"]
        if extracted.get("project_cost") and "project_cost" not in profile:
            profile["project_cost"] = extracted["project_cost"]
        if extracted.get("purpose") and "purpose" not in profile:
            profile["purpose"] = extracted["purpose"]
        if extracted.get("project_type") and "project_type" not in profile:
            profile["project_type"] = extracted["project_type"]

        # Category
        if "category" not in profile:
            cat = _extract_category(lower)
            if cat:
                profile["category"] = cat

        # Age
        if "age" not in profile:
            age = _extract_age(text)
            if age:
                profile["age"] = age

        # Gender
        if "gender" not in profile:
            gender = _extract_gender(lower)
            if gender:
                profile["gender"] = gender

        # State
        if "state" not in profile:
            state = _extract_state(lower)
            if state:
                profile["state"] = state

        # District
        if "district" not in profile:
            dist = _extract_district(text)
            if dist:
                profile["district"] = dist

        # Income
        if "annual_family_income" not in profile:
            inc = _extract_income(lower)
            if inc:
                profile["annual_family_income"] = inc

        # Occupation
        if "occupation" not in profile:
            occ = _extract_occupation(lower)
            if occ:
                profile["occupation"] = occ

        # Business sector
        if "business_sector" not in profile:
            sector = _extract_business_sector(lower)
            if sector:
                profile["business_sector"] = sector

        # Education fields
        if "course_type" not in profile:
            ct = _extract_course_type(lower)
            if ct:
                profile["course_type"] = ct

        if "education_level" not in profile:
            el = _extract_education_level(lower)
            if el:
                profile["education_level"] = el

    return profile


# ===================================================================
# Extraction helpers
# ===================================================================

def _extract_category(text: str) -> str | None:
    # Word-boundary match to avoid "st" matching inside "start", "business", etc.
    for keyword, cat in _CATEGORY_MAP.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            return cat
    # Check for "category/caste is X" patterns
    m = re.search(r"(?:category|caste|जाति)\s*(?:is|:|=|है)?\s*([A-Za-z\u0900-\u097F]+)", text)
    if m:
        val = m.group(1).lower().strip(".")
        return _CATEGORY_MAP.get(val)
    return None


def _extract_age(text: str) -> int | None:
    m = re.search(r"(\d{1,3})\s*(?:years?|yr|साल|वर्ष|yo|age|आयु|उम्र)", text, re.IGNORECASE)
    if m:
        age = int(m.group(1))
        if 18 <= age <= 100:
            return age
    m = re.search(r"(?:age|आयु|उम्र)\s*(?:is|:|=|है)?\s*(\d{1,3})", text, re.IGNORECASE)
    if m:
        age = int(m.group(1))
        if 18 <= age <= 100:
            return age
    return None


def _extract_gender(text: str) -> str | None:
    if re.search(r"\b(male|पुरुष|महिला|woman|female|girl|boy|men|women)\b", text):
        if re.search(r"\b(female|woman|women|girl|महिला|औरत|लड़की)\b", text):
            return "female"
        if re.search(r"\b(male|man|men|boy|पुरुष|आदमी|लड़का)\b", text):
            return "male"
    return None


def _extract_state(text: str) -> str | None:
    for state in _INDIAN_STATES:
        if state in text:
            return state.title()
    return None


def _extract_district(text: str) -> str | None:
    m = re.search(r"(?:district|जिला|जिल्हा)\s*(?:is|:|=|है)?\s*([A-Za-z\u0900-\u097F\s]+)", text)
    if m:
        return m.group(1).strip()[:50]
    return None


def _extract_income(text: str) -> float | None:
    """Extract an annual family income figure, handling amount-before or after keyword."""
    lower = text.lower()
    amount_re = r"(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>lakh|lakhs|लाख|lac|crore|करोड़|thousand|हजार|k)?"
    income_kw = r"(?:annual\s*family\s*income|family\s*income|annual\s*income|income|आय|कमाई|वेतन|salary|earn)"

    # Keyword then amount: "my annual family income is 2 lakh"
    m = re.search(rf"{income_kw}.{{0,30}}?{amount_re}", lower)
    if not m:
        # Amount then keyword: "2 lakh annual income"
        m = re.search(rf"{amount_re}\s*{income_kw}", lower)
    if not m:
        return None

    value = float(m.group("num").replace(",", ""))
    unit = (m.group("unit") or "").lower()
    if unit in ("lakh", "lakhs", "लाख", "lac"):
        value *= 100000
    elif unit in ("crore", "करोड़"):
        value *= 10000000
    elif unit in ("thousand", "हजार"):
        value *= 1000
    return round(value)


def _extract_occupation(text: str) -> str | None:
    occ_map = {
        "safai": "Safai Karamchari (sanitation worker)",
        "sanitation": "Safai Karamchari (sanitation worker)",
        "scavenger": "Scavenger",
        "scaveng": "Scavenger",
        "shg": "Self-Help Group member",
        "self-help": "Self-Help Group member",
        "महिला स्वयं": "Self-Help Group member",
    }
    for kw, occ in occ_map.items():
        if kw in text:
            return occ
    return None


def _extract_business_sector(text: str) -> str | None:
    sector_map = {
        "agriculture": "Agriculture & Allied",
        "kisan": "Agriculture & Allied",
        "farming": "Agriculture & Allied",
        "dairy": "Agriculture & Allied",
        "poultry": "Agriculture & Allied",
        "fish": "Agriculture & Allied",
        "beauty": "Services",
        "salon": "Services",
        "tailor": "Textile & Garment",
        "sewing": "Textile & Garment",
        "सिलाई": "Textile & Garment",
        "manufactur": "Manufacturing",
        "निर्माण": "Manufacturing",
        "shop": "Trade & Commerce",
        "retail": "Trade & Commerce",
        "दुकान": "Trade & Commerce",
        "transport": "Transport",
        "auto": "Transport",
    }
    for kw, sector in sector_map.items():
        if kw in text:
            return sector
    return None


def _extract_course_type(text: str) -> str | None:
    if re.search(r"\b(professional|engineer|medical|mbbs|btech|mtech|llb|mba|ca)\b", text):
        return "professional"
    if re.search(r"\b(technical|diploma|iti|vocational)\b", text):
        return "technical"
    if re.search(r"\b(arts|ba|bcom|bsc|ma|msc|mcom|general)\b", text):
        return "general"
    if re.search(r"\b(phd|research|mphil)\b", text):
        return "research"
    return None


def _extract_education_level(text: str) -> str | None:
    if re.search(r"\b(phd|doctorate|mphil)\b", text):
        return "phd"
    if re.search(r"\b(masters?|post.?grad|ma|msc|mcom|mtech|mba)\b", text):
        return "postgraduate"
    if re.search(r"\b(bachelors?|graduat\w*|ba|bsc|bcom|btech|bba|bca|llb)\b", text):
        return "graduate"
    if re.search(r"\b(12|12th|senior secondary|xii|intermediate)\b", text):
        return "senior_secondary"
    if re.search(r"\b(10|10th|secondary|matric)\b", text):
        return "secondary"
    return None


# ===================================================================
# Goal detection
# ===================================================================

def _detect_goal(lower: str, profile: dict) -> str:
    """Determine the user's primary goal from the latest message and profile."""
    if any(kw in lower for kw in _GOAL_EDUCATION):
        return "education"
    if any(kw in lower for kw in _GOAL_SKILL):
        return "skill"
    if any(kw in lower for kw in _GOAL_SANITATION):
        return "sanitation"
    if any(kw in lower for kw in _GOAL_BUSINESS_EXISTING):
        return "business_existing"
    if any(kw in lower for kw in _GOAL_BUSINESS_NEW):
        return "business_new"
    # Infer from profile
    if profile.get("purpose") == "education":
        return "education"
    if profile.get("purpose") in ("business", "self_employment"):
        return "business_new"
    return "general"


def _detect_intent(text: str) -> str:
    """Detect special-purpose intents (emi, documents, partner, why)."""
    emi_kw = ["emi", "installment", "ekmisi", "किस्त", "monthly payment", "repay"]
    docs_kw = ["document", "कागज", "दस्तावेज़", "documentation", "papers"]
    why_kw = ["why", "recommended", "क्यों", "सिफारिश", "matches", "reason"]
    partner_kw = ["partner", "channel partner", "nearby", "bank", "branch",
                  "पार्टनर", "चैनल", "बैंक", "where to apply", "कहाँ आवेदन"]
    for kw in emi_kw:
        if kw in text:
            return "emi"
    for kw in docs_kw:
        if kw in text:
            return "documents"
    for kw in why_kw:
        if kw in text:
            return "why"
    for kw in partner_kw:
        if kw in text:
            return "partner"
    return "scheme"


# ===================================================================
# Guided flow helpers
# ===================================================================

def _need_more_info(profile: dict, goal: str) -> str | None:
    """Return the next missing profile field name, or None when we have enough."""
    if goal == "education":
        required = ["category", "annual_family_income"]
        nice = ["age", "state", "education_level", "course_type"]
    elif goal in ("business_new", "business_existing"):
        required = ["category", "annual_family_income"]
        nice = ["age", "gender", "state", "project_cost", "requested_loan"]
    elif goal == "sanitation":
        required = ["category"]
        nice = ["age", "gender", "state", "annual_family_income"]
    elif goal == "skill":
        required = ["category"]
        nice = ["age", "gender", "state", "annual_family_income"]
    else:
        required = ["purpose"]
        nice = ["category", "age", "annual_family_income"]

    for field in required:
        if field not in profile:
            return field
    for field in nice:
        if field not in profile:
            return field
    return None


def _question_for(field: str, language: str = "en") -> str:
    """Return the next question for a missing profile field."""
    questions_en = {
        "purpose": "What are you looking for help with?\n\n1. Starting a new business\n2. Expanding an existing business\n3. Education / studies\n4. Skill training\n5. Sanitation / green business",
        "category": "What is your social category? (SC / ST / OBC / EBC / General)",
        "age": "What is your age?",
        "gender": "What is your gender? (male / female)",
        "annual_family_income": "What is your approximate annual family income? (e.g., ₹2 lakh, ₹3.5 lakh)",
        "state": "Which state are you from?",
        "district": "Which district? (optional but helps find nearby support)",
        "project_cost": "What is the estimated project cost? (e.g., ₹1.5 lakh)",
        "requested_loan": "How much loan do you need? (e.g., ₹1 lakh)",
        "occupation": "What is your occupation? (e.g., sanitation worker, tailor, farmer)",
        "business_sector": "What business sector are you in or interested in? (e.g., dairy, manufacturing, retail, services)",
        "education_level": "What is your current education level? (e.g., 10th, 12th, graduate, postgraduate)",
        "course_type": "What type of course? (professional / technical / general)",
    }
    questions_hi = {
        "purpose": "आप किस चीज़ के लिए सहायता चाहते हैं?\n\n1. नया व्यवसाय शुरू करना\n2. मौजूदा व्यवसाय का विस्तार\n3. शिक्षा / पढ़ाई\n4. कौशल प्रशिक्षण\n5. स्वच्छता / हरित व्यवसाय",
        "category": "आपका सामाजिक वर्ग क्या है? (SC / ST / OBC / EBC / सामान्य)",
        "age": "आपकी आयु क्या है?",
        "gender": "आपका लिंग क्या है? (पुरुष / महिला)",
        "annual_family_income": "आपकी वार्षिक पारिवारिक आय लगभग कितनी है? (जैसे, ₹2 लाख, ₹3.5 लाख)",
        "state": "आप किस राज्य से हैं?",
        "district": "कौन सा जिला? (वैकल्पिक लेकिन निकटतम सहायता खोजने में मदद करता है)",
        "project_cost": "अनुमानित परियोजना लागत क्या है? (जैसे, ₹1.5 लाख)",
        "requested_loan": "आपको कितने ऋण की आवश्यकता है? (जैसे, ₹1 लाख)",
        "occupation": "आपका पेशा क्या है? (जैसे, सफाई कर्मचारी, दर्जी, किसान)",
        "business_sector": "आप किस व्यवसाय क्षेत्र में हैं या रुचि रखते हैं? (जैसे, डेयरी, निर्माण, खुदरा, सेवाएँ)",
        "education_level": "आपकी वर्तमान शैक्षिक योग्यता क्या है? (जैसे, 10वीं, 12वीं, स्नातक, स्नातकोत्तर)",
        "course_type": "कोर्स का प्रकार क्या है? (पेशेवर / तकनीकी / सामान्य)",
    }
    q = questions_en.get(field, questions_en["purpose"])
    if language == "hi":
        q = questions_hi.get(field, questions_hi["purpose"])
    return q


def _parse_purpose_from_answer(text: str) -> str | None:
    """Parse a numbered answer or free text into a purpose."""
    lower = text.lower().strip()
    if re.search(r"\b1\b|new business|नया|शुरू", lower):
        return "business"
    if re.search(r"\b2\b|expand|विस्तार|existing", lower):
        return "business"
    if re.search(r"\b3\b|education|शिक्षा|study|पढ़ाई", lower):
        return "education"
    if re.search(r"\b4\b|skill|कौशल|training|प्रशिक्षण", lower):
        return "skill_training"
    if re.search(r"\b5\b|sanitation|स्वच्छता|green", lower):
        return "business"
    return None


# ===================================================================
# Intent handlers
# ===================================================================

def _handle_emi(text: str, profile: dict, language: str, db: Session) -> dict:
    """Handle EMI estimation questions using the recommendation engine's scheme data."""
    # Try to find a specific scheme from conversation context
    scheme_row = _find_scheme_from_context(text, db)

    if scheme_row and scheme_row.interest_rate is not None:
        # Use the scheme's actual verified rate
        loan = profile.get("requested_loan") or scheme_row.max_loan or 100000
        loan = min(loan, scheme_row.max_loan or 2000000)
        calc = calculate_loan(
            loan,
            scheme_row.interest_rate,
            scheme_row.tenure_months or 36,
            "months",
            scheme_row.moratorium_months or 0,
        )
        return _reply(
            language,
            en=(
                f"**{scheme_row.name}** — estimated EMI:\n\n"
                f"Loan amount: ₹{loan:,.0f}\n"
                f"Interest rate: {scheme_row.interest_rate}% p.a.\n"
                f"Tenure: {scheme_row.tenure_months or 36} months\n"
                f"Estimated monthly EMI: **₹{calc['emi']:,.2f}**\n"
                f"Total interest: ₹{calc['total_interest']:,.2f}\n"
                f"Total repayment: ₹{calc['total_repayment']:,.2f}\n\n"
                f"These are estimates based on the current verified official rate. "
                f"Actual terms may vary. Verify before applying."
            ),
            hi=(
                f"**{scheme_row.name}** — अनुमानित EMI:\n\n"
                f"ऋण राशि: ₹{loan:,.0f}\n"
                f"ब्याज दर: {scheme_row.interest_rate}% प्रति वर्ष\n"
                f"अवधि: {scheme_row.tenure_months or 36} महीने\n"
                f"अनुमानित मासिक EMI: **₹{calc['emi']:,.2f}**\n"
                f"कुल ब्याज: ₹{calc['total_interest']:,.2f}\n"
                f"कुल भुगतान: ₹{calc['total_repayment']:,.2f}\n\n"
                f"ये अनुमान वर्तमान सत्यापित आधिकारिक दर पर आधारित हैं। "
                f"वास्तविक शर्तें भिन्न हो सकती हैं। आवेदन करने से पहले सत्यापित करें।"
            ),
        )

    if scheme_row and scheme_row.interest_rate is None and scheme_row.interest_tiers:
        # Tiered rate — show the tiers instead of inventing a flat rate
        tiers = [t for t in scheme_row.interest_tiers if isinstance(t, dict)]
        tier_lines = []
        for t in tiers:
            rate = t.get("interest_rate", "?")
            if t.get("loan_up_to"):
                tier_lines.append(f"  • Up to ₹{t['loan_up_to']:,.0f}: {rate}% p.a.")
            elif t.get("channel"):
                tier_lines.append(f"  • {t['channel']}: {rate}% p.a.")
            else:
                tier_lines.append(f"  • {rate}% p.a.")
        tier_text = "\n".join(tier_lines)
        loan = profile.get("requested_loan") or 100000
        return _reply(
            language,
            en=(
                f"**{scheme_row.name}** uses tiered interest rates:\n{tier_text}\n\n"
                f"For a loan of ₹{loan:,.0f}, the applicable rate depends on the "
                f"specific slab/channel. Please check the official scheme page or the "
                f"channelizing agency for the exact rate.\n\n"
                "An accurate EMI cannot be calculated without knowing the exact applicable tier."
            ),
            hi=(
                f"**{scheme_row.name}** में स्तरित ब्याज दरें हैं:\n{tier_text}\n\n"
                f"₹{loan:,.0f} के ऋण के लिए लागू दर विशिष्ट स्लैब/चैनल पर निर्भर करती है। "
                f"सटीक दर के लिए आधिकारिक योजना पृष्ठ या चैनलाइजिंग एजेंसी से जांच करें।\n\n"
                "सही EMI की गणना लागू स्तर ज्ञात किए बिना नहीं की जा सकती।"
            ),
        )

    # No specific scheme found — use a general explanation
    loan = profile.get("requested_loan") or 100000
    loan = min(loan, 2000000)
    return _reply(
        language,
        en=(
            "An accurate EMI cannot be calculated from the currently verified data "
            "because no specific scheme with a confirmed rate has been identified yet.\n\n"
            "Please tell me which scheme you are interested in — or I can help you "
            "find matching schemes first, and then estimate the EMI from the "
            "verified official rate."
        ),
        hi=(
            "फिलहाल सत्यापित डेटा के आधार पर सटीक EMI की गणना नहीं की जा सकती, "
            "क्योंकि पुष्टि दर वाली कोई विशिष्ट योजना अभी पहचानी नहीं गई है।\n\n"
            "कृपया बताएं कि आप किस योजना में रुचि रखते हैं — या मैं पहले मिलान "
            "योजनाएँ खोजने में मदद कर सकता हूँ, और फिर सत्यापित आधिकारिक दर से "
            "EMI का अनुमान लगा सकता हूँ।"
        ),
    )


def _handle_documents(profile: dict, language: str, db: Session) -> dict:
    """Handle document questions using confirmed scheme data."""
    # If a scheme is in context, use its confirmed documents
    confirmed_docs = [
        "Aadhaar / identity proof",
        "Caste / category certificate (if applicable)",
        "Income certificate",
        "Bank account details",
    ]
    business_docs = [
        "Project report / business plan",
        "Proof of business address or registration",
    ]
    edu_docs = [
        "Admission letter / course enrollment proof",
        "Marksheet / academic records",
        "Fee structure from the institution",
    ]

    purpose = profile.get("purpose", "business")
    if purpose == "education":
        docs = confirmed_docs + edu_docs
    else:
        docs = confirmed_docs + business_docs

    doc_list = "\n".join(f"• {d}" for d in docs)
    return _reply(
        language,
        en=(
            f"Based on typical government scheme requirements, you may need:\n\n"
            f"{doc_list}\n\n"
            f"**Note:** The exact documents depend on the specific scheme. "
            f"A channelizing agency may request additional documents. "
            f"Check the Scheme Details page for the scheme-specific checklist."
        ),
        hi=(
            f"सरकारी योजना आवश्यकताओं के आधार पर, आपको चाहिए:\n\n"
            f"{doc_list}\n\n"
            f"**नोट:** सटीक दस्तावेज़ विशिष्ट योजना पर निर्भर करते हैं। "
            f"चैनलाइजिंग एजेंसी अतिरिक्त दस्तावेज़ मांग सकती है। "
            f"योजना-विशिष्ट सूची के लिए योजना विवरण पृष्ठ देखें।"
        ),
    )


def _handle_partner(profile: dict, language: str, db: Session) -> dict:
    """Handle partner/channel partner questions."""
    partner_profile = {
        "purpose": profile.get("purpose", "business"),
        "state": profile.get("state"),
        "district": profile.get("district"),
    }
    scored = route_partners(partner_profile, db)
    if not scored:
        return _reply(
            language,
            en="No channel partners are currently available in the demo database. In production, partners near your location would appear here.",
            hi="डेमो डेटाबेस में अभी कोई चैनल पार्टनर उपलब्ध नहीं है। प्रोडक्शन में, आपके पास के पार्टनर यहाँ दिखाई देंगे।",
        )
    top = scored[0]
    partner = top["partner"]
    return _reply(
        language,
        en=(
            f"**Nearest channel partner:** {partner.name} ({partner.type})\n"
            f"Location: {partner.city}, {partner.district}, {partner.state}\n"
            f"Phone: {partner.phone}\n"
            f"Status: {partner.status}\n\n"
            f"This is based on routing score {top['total']}/100. "
            f"In production, more partners near your location would appear."
        ),
        hi=(
            f"**निकटतम चैनल पार्टनर:** {partner.name} ({partner.type})\n"
            f"स्थान: {partner.city}, {partner.district}, {partner.state}\n"
            f"फ़ोन: {partner.phone}\n"
            f"स्थिति: {partner.status}\n\n"
            f"यह रूटिंग स्कोर {top['total']}/100 पर आधारित है।"
        ),
    )


def _handle_why(profile: dict, language: str, db: Session) -> dict:
    """Explain why a scheme was recommended using DB-driven reasons."""
    if not profile.get("purpose"):
        return _reply(
            language,
            en="I need to know your purpose first. Tell me what you're looking for — a business loan, education support, etc.",
            hi="मुझे पहले आपका उद्देश्य जानना होगा। बताएं आप क्या खोज रहे हैं — व्यवसाय ऋण, शिक्षा सहायता, आदि।",
        )

    # Build a profile for the recommendation engine
    rec_profile = {
        "purpose": profile.get("purpose", "business"),
        "category": profile.get("category"),
        "annual_family_income": profile.get("annual_family_income"),
        "age": profile.get("age"),
        "gender": profile.get("gender"),
        "state": profile.get("state"),
        "district": profile.get("district"),
        "project_cost": profile.get("project_cost"),
        "requested_loan": profile.get("requested_loan"),
        "occupation": profile.get("occupation"),
    }
    result = recommend_full(rec_profile, db, official_only=True)
    matches = result.get("primary_matches", [])

    if not matches:
        return _reply(
            language,
            en=(
                "I haven't found matching schemes yet. This could be because:\n"
                "• Some required information is missing (category, income, state)\n"
                "• Your profile may not match the targeted groups of available schemes\n\n"
                "Try sharing more details about your profile and requirements."
            ),
            hi=(
                "मुझे अभी तक मिलान योजनाएँ नहीं मिली हैं। इसके कारण:\n"
                "• कुछ आवश्यक जानकारी गायब है (वर्ग, आय, राज्य)\n"
                "• आपकी प्रोफ़ाइल उपलब्ध योजनाओं के लक्षित समूहों से मेल नहीं खाती\n\n"
                "अपनी प्रोफ़ाइल और आवश्यकताओं के बारे में और बताएं।"
            ),
        )

    top = matches[0]
    reasons = top.get("reasons", [])
    matched_fields = top.get("matched", [])
    status = top.get("eligibility_status", "eligible")
    confidence = top.get("data_confidence", "needs_review")
    source_url = top.get("official_scheme_url") or top.get("source_url")
    verified = confidence == "verified"

    reasons_text = "\n".join(f"• {r}" for r in reasons[:5])
    matched_text = "\n".join(f"  ✓ {f}" for f in matched_fields[:5])

    confidence_note = (
        "Based on the current verified official source."
        if verified
        else "Source is official, but some details require manual verification."
    )

    en = (
        f"**{top.get('scheme_name', 'Top match')}** was recommended because:\n\n"
        f"Why it matches:\n{reasons_text}\n\n"
        f"Matched criteria:\n{matched_text}\n\n"
        f"Match score: {top.get('match_score', 0)}% "
        f"(status: {status})\n\n"
        f"{confidence_note}\n"
    )
    if source_url:
        en += f"\nOfficial source: {source_url}"
    if top.get("last_verified"):
        en += f"\nLast verified: {top['last_verified']}"

    hi = (
        f"**{top.get('scheme_name', 'शीर्ष मिलान')}** निम्न कारणों से अनुशंसित है:\n\n"
        f"क्यों मिलता है:\n{reasons_text}\n\n"
        f"मिलान मापदंड:\n{matched_text}\n\n"
        f"मिलान स्कोर: {top.get('match_score', 0)}% "
        f"(स्थिति: {status})\n\n"
        f"{confidence_note}\n"
    )
    if source_url:
        hi += f"\nआधिकारिक स्रोत: {source_url}"
    if top.get("last_verified"):
        hi += f"\nअंतिम सत्यापन: {top['last_verified']}"

    return _reply(language, en, hi)


# ===================================================================
# Goal-based guided flows
# ===================================================================

def _handle_business_flow(
    user_msgs: list[dict], profile: dict, goal: str, language: str, db: Session
) -> dict:
    """Step-by-step business guidance."""
    missing = _need_more_info(profile, "business_new")
    if missing:
        step = _count_gathered(profile)
        total = 7
        intro_en, intro_hi = (
            "Let me help you find the right scheme for your business.\n\n",
            "मैं आपके व्यवसाय के लिए सही योजना खोजने में मदद करता हूँ।\n\n",
        )
        return _reply_with_step(
            language, step, total,
            en=intro_en + _question_for(missing, "en"),
            hi=intro_hi + _question_for(missing, "hi"),
        )

    # Enough info — run recommendation
    rec_profile = _build_rec_profile(profile)
    result = recommend_full(rec_profile, db, official_only=True)
    matches = result.get("primary_matches", [])
    support = result.get("complementary_support", [])

    if not matches:
        no_reason = result.get("no_match_reason", "")
        return _reply(
            language,
            en=(
                f"I checked the available government schemes with the information provided, "
                f"but no strong match was found.\n\n"
                f"{no_reason}\n\n"
                f"You can try:\n"
                f"• Sharing more details (category, income, state)\n"
                f"• Checking the Eligibility page for a detailed check"
            ),
            hi=(
                f"मैंने दी गई जानकारी के साथ उपलब्ध सरकारी योजनाओं की जांच की, "
                f"लेकिन कोई मजबूत मिलान नहीं मिला।\n\n"
                f"{no_reason}\n\n"
                f"आप ये कोशिश कर सकते हैं:\n"
                f"• और जानकारी साझा करें (वर्ग, आय, राज्य)\n"
                f"• पात्रता पृष्ठ पर विस्तृत जांच करें"
            ),
        )

    return _format_scheme_results(matches, support, language, "business")


def _handle_education_flow(
    user_msgs: list[dict], profile: dict, language: str, db: Session
) -> dict:
    """Step-by-step education guidance."""
    missing = _need_more_info(profile, "education")
    if missing:
        step = _count_gathered(profile)
        total = 7
        intro_en, intro_hi = (
            "Let me help you find education loan schemes.\n\n",
            "मैं शिक्षा ऋण योजनाएँ खोजने में मदद करता हूँ।\n\n",
        )
        return _reply_with_step(
            language, step, total,
            en=intro_en + _question_for(missing, "en"),
            hi=intro_hi + _question_for(missing, "hi"),
        )

    profile["purpose"] = "education"
    rec_profile = _build_rec_profile(profile)
    result = recommend_full(rec_profile, db, official_only=True)
    matches = result.get("primary_matches", [])
    support = result.get("complementary_support", [])

    if not matches:
        return _reply(
            language,
            en=(
                "I checked education loan schemes with your details, but no strong match was found.\n\n"
                "Education loan schemes typically require:\n"
                "• Enrollment in a recognized institution\n"
                "• Family income within the scheme ceiling\n"
                "• Appropriate academic qualifications\n\n"
                "Try sharing more details or check the Eligibility page."
            ),
            hi=(
                "मैंने आपकी जानकारी के साथ शिक्षा ऋण योजनाओं की जांच की, लेकिन कोई मजबूत मिलान नहीं मिला।\n\n"
                "शिक्षा ऋण योजनाओं के लिए आमतौर पर चाहिए:\n"
                "• मान्यता प्राप्त संस्थान में नामांकन\n"
                "• योजना सीमा के भीतर पारिवारिक आय\n"
                "• उपयुक्त शैक्षणिक योग्यता\n\n"
                "और जानकारी साझा करें या पात्रता पृष्ठ देखें।"
            ),
        )

    return _format_scheme_results(matches, support, language, "education")


def _handle_sanitation_flow(profile: dict, language: str, db: Session) -> dict:
    """Handle sanitation/green business queries — mention NSKFDC + PM-DAKSH."""
    rec_profile = _build_rec_profile(profile)
    rec_profile["purpose"] = "business"
    result = recommend_full(rec_profile, db, official_only=True)
    matches = result.get("primary_matches", [])
    support = result.get("complementary_support", [])

    parts = []
    if language == "en":
        parts.append("Sanitation and green business schemes are available through NSKFDC and other government programmes.\n")
    else:
        parts.append("स्वच्छता और हरित व्यवसाय योजनाएँ NSKFDC और अन्य सरकारी कार्यक्रमों के माध्यम से उपलब्ध हैं।\n")

    if matches:
        return _format_scheme_results(matches, support, language, "sanitation")

    return _reply(
        language,
        en=(
            "Sanitation and green business schemes are available through NSKFDC "
            "for Safai Karamcharis and related occupations.\n\n"
            "PM-DAKSH also provides skill development support for sanitation workers.\n\n"
            "To find the right scheme, I need to know:\n"
            "• Your social category (SC/ST/OBC/etc.)\n"
            "• Your occupation\n"
            "• Your state"
        ),
        hi=(
            "स्वच्छता और हरित व्यवसाय योजनाएँ NSKFDC द्वारा सफाई कर्मचारियों और "
            "संबंधित पेशों के लिए उपलब्ध हैं।\n\n"
            "PM-DAKSH सफाई कर्मचारियों के लिए कौशल विकास सहायता भी प्रदान करता है।\n\n"
            "सही योजना खोजने के लिए, मुझे जानना होगा:\n"
            "• आपका सामाजिक वर्ग (SC/ST/OBC/आदि)\n"
            "• आपका पेशा\n"
            "• आपका राज्य"
        ),
    )


def _handle_skill_flow(profile: dict, language: str, db: Session) -> dict:
    """Handle skill/training queries — mention PM-DAKSH."""
    return _reply(
        language,
        en=(
            "**PM-DAKSH** is a government skill development programme for:\n"
            "• SC/OBC/EBC candidates\n"
            "• Safai Karamcharis and waste pickers\n"
            "• De-notified tribes\n"
            "• Age 18–45 years\n\n"
            "It provides training with a monthly stipend (₹3,000–₹15,000 depending on course level).\n\n"
            "This is a **support programme** (training), not a loan.\n\n"
            "To check your eligibility, I need:\n"
            "• Your social category\n"
            "• Your age\n"
            "• Your state"
        ),
        hi=(
            "**PM-DAKSH** एक सरकारी कौशल विकास कार्यक्रम है:\n"
            "• SC/OBC/EBC उम्मीदवारों के लिए\n"
            "• सफाई कर्मचारियों और कचरा बीनने वालों के लिए\n"
            "• अधिसूचित जनजातियों के लिए\n"
            "• आयु 18-45 वर्ष\n\n"
            "यह मासिक वजीफा प्रदान करता है (कोर्स स्तर के अनुसार ₹3,000-₹15,000)।\n\n"
            "यह एक **सहायता कार्यक्रम** (प्रशिक्षण) है, ऋण नहीं।\n\n"
            "पात्रता जांचने के लिए, मुझे चाहिए:\n"
            "• आपका सामाजिक वर्ग\n"
            "• आपकी आयु\n"
            "• आपका राज्य"
        ),
    )


# ===================================================================
# Default guided flow (when goal is unclear)
# ===================================================================

def _handle_guided_flow(
    user_msgs: list[dict], profile: dict, language: str, db: Session
) -> dict:
    """General guided flow — determine what the user wants and help them."""
    # If we have a purpose, try to gather more and eventually recommend
    if profile.get("purpose"):
        missing = _need_more_info(profile, profile["purpose"])
        if missing:
            step = _count_gathered(profile)
            total = 7
            return _reply_with_step(
                language, step, total,
                en=f"Great, I can help with that. Let me gather a few more details.\n\n{missing}",
                hi=f"बहुत अच्छा, मैं इसमें मदद कर सकता हूँ। कुछ और विवरण एकत्र करते हैं।\n\n{missing}",
            )

        # Enough info — recommend
        rec_profile = _build_rec_profile(profile)
        result = recommend_full(rec_profile, db, official_only=True)
        matches = result.get("primary_matches", [])
        support = result.get("complementary_support", [])

        if matches:
            return _format_scheme_results(matches, support, language, profile["purpose"])
        else:
            return _reply(
                language,
                en=(
                    "I checked the available government schemes, but no strong match was found with the details provided.\n\n"
                    "Try sharing more about your:\n"
                    "• Social category (SC/ST/OBC/EBC/General)\n"
                    "• Annual family income\n"
                    "• State and district\n"
                    "• Specific requirements"
                ),
                hi=(
                    "मैंने उपलब्ध सरकारी योजनाओं की जांच की, लेकिन दिए गए विवरण से कोई मजबूत मिलान नहीं मिला।\n\n"
                    "अपने बारे में और बताएं:\n"
                    "• सामाजिक वर्ग (SC/ST/OBC/EBC/सामान्य)\n"
                    "• वार्षिक पारिवारिक आय\n"
                    "• राज्य और जिला\n"
                    "• विशिष्ट आवश्यकताएँ"
                ),
            )

    # No purpose detected yet — ask what they need
    if not profile:
        return _reply(
            language,
            en=(
                "Welcome! I can help you with:\n\n"
                "• **Business loan** — starting or expanding a business\n"
                "• **Education loan** — studies and courses\n"
                "• **Skill training** — PM-DAKSH and vocational programmes\n"
                "• **Sanitation business** — NSKFDC schemes for Safai Karamcharis\n\n"
                "Tell me what you're looking for, and I'll guide you step by step."
            ),
            hi=(
                "स्वागत है! मैं इसमें मदद कर सकता हूँ:\n\n"
                "• **व्यवसाय ऋण** — व्यवसाय शुरू करना या विस्तार करना\n"
                "• **शिक्षा ऋण** — पढ़ाई और कोर्स\n"
                "• **कौशल प्रशिक्षण** — PM-DAKSH और व्यावसायिक कार्यक्रम\n"
                "• **स्वच्छता व्यवसाय** — NSKFDC योजनाएँ सफाई कर्मचारियों के लिए\n\n"
                "मुझे बताएं आप क्या खोज रहे हैं, और मैं आपको चरण दर चरण मार्गदर्शन दूंगा।"
            ),
        )

    # Partial info — ask for the missing pieces
    missing = _need_more_info(profile, "general")
    if missing:
        return _reply(language, en=_question_for(missing, "en"), hi=_question_for(missing, "hi"))

    return _reply(
        language,
        en="Tell me more about what you need help with — business loan, education, or skill training?",
        hi="बताएं आपको किस चीज़ में मदद चाहिए — व्यवसाय ऋण, शिक्षा, या कौशल प्रशिक्षण?",
    )


# ===================================================================
# Scheme result formatting
# ===================================================================

def _format_scheme_results(
    matches: list[dict], support: list[dict], language: str, context: str
) -> dict:
    """Format recommendation results with explanations, source transparency, and warnings."""
    top_n = matches[:3]
    parts = []

    if language == "en":
        parts.append("Based on the information you provided, these schemes may fit you:\n")
    else:
        parts.append("आपके द्वारा दी गई जानकारी के आधार पर, ये योजनाएँ आपके लिए उपयुक्त हो सकती हैं:\n")

    for i, m in enumerate(top_n, 1):
        name = m.get("scheme_name", "Scheme")
        score = m.get("match_score", 0)
        status = m.get("eligibility_status", "eligible")
        confidence = m.get("data_confidence", "needs_review")
        reasons = m.get("reasons", [])
        max_loan = m.get("max_loan")
        interest = m.get("interest_display") or m.get("interest_rate")
        source_url = m.get("official_scheme_url") or m.get("source_url")
        verified = confidence == "verified"

        if language == "en":
            parts.append(f"**{i}. {name}**")
            parts.append(f"   Match: {score}% ({status})")
            if max_loan:
                parts.append(f"   Max loan: ₹{max_loan:,.0f}")
            if interest:
                parts.append(f"   Interest: {interest}")
            if reasons:
                parts.append("   Why it matches:")
                for r in reasons[:4]:
                    parts.append(f"     • {r}")
            if verified:
                parts.append("   ✓ Based on verified official source")
            else:
                parts.append("   ⚠ Source is official, but some details need manual verification")
            if source_url:
                parts.append(f"   Source: {source_url}")
            if m.get("last_verified"):
                parts.append(f"   Last verified: {m['last_verified']}")
            parts.append("")
        else:
            parts.append(f"**{i}. {name}**")
            parts.append(f"   मिलान: {score}% ({status})")
            if max_loan:
                parts.append(f"   अधिकतम ऋण: ₹{max_loan:,.0f}")
            if interest:
                parts.append(f"   ब्याज: {interest}")
            if reasons:
                parts.append("   क्यों मिलता है:")
                for r in reasons[:4]:
                    parts.append(f"     • {r}")
            if verified:
                parts.append("   ✓ सत्यापित आधिकारिक स्रोत पर आधारित")
            else:
                parts.append("   ⚠ स्रोत आधिकारिक है, लेकिन कुछ विवरणों की मैनुअल जांच आवश्यक है")
            if source_url:
                parts.append(f"   स्रोत: {source_url}")
            if m.get("last_verified"):
                parts.append(f"   अंतिम सत्यापन: {m['last_verified']}")
            parts.append("")

    # Complementary support
    if support:
        if language == "en":
            parts.append("**Additional Government Support** (not loans):\n")
        else:
            parts.append("**अतिरिक्त सरकारी सहायता** (ऋण नहीं):\n")
        for s in support[:2]:
            name = s.get("scheme_name", "Support programme")
            if language == "en":
                parts.append(f"• {name} — skill development / training support")
            else:
                parts.append(f"• {name} — कौशल विकास / प्रशिक्षण सहायता")
        parts.append("")

    # Disclaimer
    if language == "en":
        parts.append(
            "Important: Please verify the latest official conditions before applying. "
            "Financial and eligibility facts come from the official scheme database."
        )
    else:
        parts.append(
            "महत्वपूर्ण: आवेदन करने से पहले नवीनतम आधिकारिक शर्तों की जांच करें। "
            "वित्तीय और पात्रता तथ्य आधिकारिक योजना डेटाबेस से आते हैं।"
        )

    text = "\n".join(parts)

    # Build structured data for frontend cards
    structured = []
    for m in top_n:
        structured.append({
            "scheme_slug": m.get("scheme_slug"),
            "scheme_name": m.get("scheme_name"),
            "match_score": m.get("match_score", 0),
            "eligibility_status": m.get("eligibility_status"),
            "data_confidence": m.get("data_confidence"),
            "max_loan": m.get("max_loan"),
            "interest_display": m.get("interest_display"),
            "official_scheme_url": m.get("official_scheme_url"),
            "last_verified": m.get("last_verified"),
            "reasons": m.get("reasons", [])[:4],
            "is_loan": m.get("is_loan", True),
        })

    return {
        "message": text,
        "language": language,
        "suggestions": SUGGESTIONS,
        "structured": structured,
    }


# ===================================================================
# Helpers
# ===================================================================

def _build_rec_profile(profile: dict) -> dict:
    """Build a recommendation engine profile from the gathered conversation profile."""
    return {
        "purpose": profile.get("purpose", "business"),
        "category": profile.get("category"),
        "annual_family_income": profile.get("annual_family_income"),
        "age": profile.get("age"),
        "gender": profile.get("gender"),
        "state": profile.get("state"),
        "district": profile.get("district"),
        "project_cost": profile.get("project_cost"),
        "requested_loan": profile.get("requested_loan"),
        "occupation": profile.get("occupation"),
        "business_sector": profile.get("business_sector"),
        "course_type": profile.get("course_type"),
        "education_level": profile.get("education_level"),
    }


def _find_scheme_from_context(text: str, db: Session) -> Scheme | None:
    """Try to find a scheme mentioned by name or slug in the text."""
    lower = text.lower()
    # Direct slug match
    schemes = db.query(Scheme).filter(Scheme.active.is_(True)).all()
    for s in schemes:
        if s.slug.lower() in lower or s.name.lower() in lower:
            return s
        short = (s.short_name or "").lower()
        if short and short in lower:
            return s
    return None


def _count_gathered(profile: dict) -> int:
    """Count how many profile fields have been gathered."""
    fields = [
        "purpose", "category", "age", "gender", "annual_family_income",
        "state", "district", "project_cost", "requested_loan",
        "occupation", "business_sector", "course_type", "education_level",
    ]
    return sum(1 for f in fields if f in profile)


def _reply(language: str, en: str, hi: str) -> dict:
    text = hi if language == "hi" else en
    return {
        "message": text,
        "language": language,
        "suggestions": SUGGESTIONS,
        "structured": None,
    }


def _reply_with_step(language: str, step: int, total: int, en: str, hi: str) -> dict:
    text = hi if language == "hi" else en
    # Prepend step indicator
    step_en = f"[Step {step}/{total}]\n\n"
    step_hi = f"[चरण {step}/{total}]\n\n"
    prefix = step_hi if language == "hi" else step_en
    return {
        "message": prefix + text,
        "language": language,
        "suggestions": SUGGESTIONS,
        "structured": None,
        "step": step,
        "total_steps": total,
    }


def _greeting_en() -> str:
    return (
        "Welcome! I can help you with:\n\n"
        "• **Business loan** — starting or expanding a business\n"
        "• **Education loan** — studies and courses\n"
        "• **Skill training** — PM-DAKSH and vocational programmes\n"
        "• **Sanitation business** — NSKFDC schemes for Safai Karamcharis\n\n"
        "Tell me what you're looking for, and I'll guide you step by step."
    )


def _greeting_hi() -> str:
    return (
        "स्वागत है! मैं इसमें मदद कर सकता हूँ:\n\n"
        "• **व्यवसाय ऋण** — व्यवसाय शुरू करना या विस्तार करना\n"
        "• **शिक्षा ऋण** — पढ़ाई और कोर्स\n"
        "• **कौशल प्रशिक्षण** — PM-DAKSH और व्यावसायिक कार्यक्रम\n"
        "• **स्वच्छता व्यवसाय** — NSKFDC योजनाएँ सफाई कर्मचारियों के लिए\n\n"
        "मुझे बताएं आप क्या खोज रहे हैं, और मैं आपको चरण दर चरण मार्गदर्शन दूंगा।"
    )
