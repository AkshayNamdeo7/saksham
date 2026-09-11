"""
AI service abstraction.

Reads credentials from environment variables. When no API key is configured,
falls back to deterministic template explanations so the app remains fully
functional without an external LLM.

The AI NEVER changes the deterministic eligibility result — it only explains it.
"""

import re

import httpx

from app.core.config import settings


def _has_ai_key() -> bool:
    return bool(settings.AI_API_KEY)


def _camel_hi(value):
    return value


class AIService:
    """Optional LLM integration with deterministic fallback."""

    def __init__(self):
        self.enabled = _has_ai_key()

    # ------------------------------------------------------------------
    # Recommendation explanation
    # ------------------------------------------------------------------
    def generate_recommendation_explanation(
        self, profile: dict, result: dict, language: str = "en"
    ) -> str:
        if self.enabled:
            try:
                return self._llm_explanation(profile, result, language)
            except Exception:
                pass
        return self._template_explanation(profile, result, language)

    def _template_explanation(self, profile: dict, result: dict, language: str = "en") -> str:
        purpose = profile.get("purpose", "the stated purpose")
        reasons = result.get("reasons") or ["it meets the configured demo criteria"]
        scheme_name = result.get("scheme_name", "this scheme")
        score = result.get("match_score", 0)
        status = result.get("eligibility_status", "eligible")
        reason_text = "; ".join(reasons[:3])
        if language == "hi":
            return (
                f"आपकी जानकारी के आधार पर, {scheme_name} आपके लिए उपयुक्त प्रतीत होता है क्योंकि "
                f"आपका उद्देश्य {purpose} से संबंधित है और यह निर्धारित डेमो मानदंडों को पूरा करता है "
                f"({reason_text})। मैच स्कोर {score}% है तथा स्थिति '{status}' है। "
                "कृपया ध्यान दें: यह अनुमानित/डेमो जानकारी है, आधिकारिक दिशानिर्देशों से पुष्टि करें।"
            )
        return (
            f"Based on the information you provided, {scheme_name} appears suitable because "
            f"your purpose is {purpose}-related and it meets the configured demo criteria "
            f"({reason_text}). Your match score is {score}% with an eligibility status of "
            f"'{status}'. Please note: this is an indicative assessment; verify against "
            "official scheme guidelines."
        )

    def _llm_explanation(self, profile: dict, result: dict, language: str) -> str:
        prompt = (
            f"Explain in under 120 words, in {'Hindi' if language=='hi' else 'English'}, why the "
            f"scheme '{result.get('scheme_name')}' (match score {result.get('match_score')}%, "
            f"status {result.get('eligibility_status')}) may fit this user profile: {profile}. "
            "Use plain, reassuring, non-technical language. Do not invent eligibility rules."
        )
        return self._call_llm(prompt, language)

    # ------------------------------------------------------------------
    # Assistant chat
    # ------------------------------------------------------------------
    def assistant_reply(self, messages: list[dict], language: str = "en") -> str | None:
        if not self.enabled:
            return None
        try:
            return self._call_llm_chat(messages, language)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Low-level LLM call (OpenAI-compatible chat completions)
    # ------------------------------------------------------------------
    def _call_llm(self, prompt: str, language: str) -> str:
        return self._chat_completions(
            [{"role": "user", "content": prompt}], language=language
        )

    def _call_llm_chat(self, messages: list[dict], language: str) -> str:
        system = (
            "You are Saksham Assistant, helping marginalized entrepreneurs and students "
            "understand government concessional loan and support schemes.\n\n"
            "CRITICAL RULES:\n"
            "- NEVER invent loan amounts, interest rates, eligibility criteria, documents, "
            "or approval probability.\n"
            "- Financial and eligibility facts MUST come from the official scheme database. "
            "If information is missing, say 'Please verify before applying.'\n"
            "- If a scheme's data is marked needs_review, say clearly: "
            "'Source is official, but some details require manual verification.'\n"
            "- Support schemes (PM-DAKSH, PM-AJAY) are NOT loans. Do not call them loans.\n"
            "- For tiered interest rates, do NOT assume a flat rate. Direct users to check "
            "the official scheme page.\n"
            "- Keep responses simple, practical, step-by-step.\n"
            "- Respond in " + ("Hindi" if language == "hi" else "English") + "."
        )
        full = [{"role": "system", "content": system}] + messages[-8:]
        return self._chat_completions(full, language=language)

    def _chat_completions(self, messages: list[dict], language: str) -> str:
        url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.AI_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 400,
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()


ai_service = AIService()


# ----------------------------------------------------------------------
# Deterministic NLP-lite extraction for the assistant chatbot.
# No external dependency. Extracts structured fields from free text.
# ----------------------------------------------------------------------
PURPOSE_REGEX = {
    "business": [r"business", r"व्यवसाय", r"dairy", r"डेयरी", r"shop", r"manufactur", r"trade"],
    "self_employment": [r"self[- ]employment", r"स्वरोजगार", r"auto", r"रिक्शा", r"service", r"sewing", r"सिलाई"],
    "education": [r"study", r"course", r"college", r"शिक्षा", r"education", r"degree", r"बी\s?एड", r"coaching", r"tuition"],
}


def extract_profile_from_text(text: str) -> dict:
    lower = text.lower()
    extracted = {}

    # amount (INR)
    amount_match = re.search(
        r"(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|लाख|करोड़|crore|lac|k|हजार|thousand)?",
        lower,
    )
    if amount_match:
        value = float(amount_match.group(1).replace(",", ""))
        unit = (amount_match.group(2) or "").lower()
        if unit in ("lakh", "lakhs", "लाख", "lac"):
            value *= 100000
        elif unit in ("करोड़", "crore"):
            value *= 10000000
        elif unit in ("हजार", "thousand", "k"):
            value *= 1000
        extracted["requested_loan"] = round(value)
        extracted["project_cost"] = round(value)

    # purpose
    for purpose, patterns in PURPOSE_REGEX.items():
        if any(re.search(p, lower) for p in patterns):
            extracted["purpose"] = purpose
            break

    # project type
    dairy = re.search(r"dairy|डेयरी|पशुपालन", lower)
    if dairy:
        extracted["project_type"] = "dairy"
    elif re.search(r"manufactur|निर्माण", lower):
        extracted["project_type"] = "small_manufacturing"
    elif re.search(r"shop|दुकान", lower):
        extracted["project_type"] = "retail_shop"
    elif re.search(r"sewing|सिलाई", lower):
        extracted["project_type"] = "sewing/tailoring"
    elif re.search(r"auto|ride", lower):
        extracted["project_type"] = "auto/transport"

    # social category
    cat_match = re.search(
        r"\b(sc|st|obc|ebc|general|gen|अनुसूचित जाति|अनुसूचित जनजाति|अन्य पिछड़ा वर्ग|सामान्य)\b",
        lower,
    )
    if cat_match:
        cat_val = cat_match.group(1)
        cat_map = {
            "sc": "SC", "st": "ST", "obc": "OBC", "ebc": "EBC",
            "general": "General", "gen": "General",
            "अनुसूचित जाति": "SC", "अनुसूचित जनजाति": "ST",
            "अन्य पिछड़ा वर्ग": "OBC", "सामान्य": "General",
        }
        extracted["category"] = cat_map.get(cat_val)

    # age
    age_match = re.search(r"(\d{1,3})\s*(?:years?|yr|साल|वर्ष|yo|age|आयु|उम्र)", text, re.IGNORECASE)
    if age_match:
        age = int(age_match.group(1))
        if 18 <= age <= 100:
            extracted["age"] = age

    # gender
    if re.search(r"\b(female|woman|women|girl|महिला|औरत|लड़की)\b", lower):
        extracted["gender"] = "female"
    elif re.search(r"\b(male|man|men|boy|पुरुष|आदमी|लड़का)\b", lower):
        extracted["gender"] = "male"

    # income
    inc_match = re.search(
        r"(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|लाख|lac|crore|करोड़|thousand|हजार|k)?\s*(?:income|annual|salary|कमाई|आय|वेतन)",
        lower,
    )
    if inc_match:
        value = float(inc_match.group(1).replace(",", ""))
        unit = (inc_match.group(2) or "").lower()
        if unit in ("lakh", "lakhs", "लाख", "lac"):
            value *= 100000
        elif unit in ("crore", "करोड़"):
            value *= 10000000
        elif unit in ("thousand", "हजार", "k"):
            value *= 1000
        extracted["annual_family_income"] = round(value)

    return extracted


def detect_loan_in_message(lower: str) -> float | None:
    return extract_profile_from_text(lower).get("requested_loan")
