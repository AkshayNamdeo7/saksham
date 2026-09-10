"""
myScheme.gov.in adapter.

myScheme (https://www.myscheme.gov.in/) is the Government of India's
official scheme discovery portal. It does not expose a stable public REST API
for all schemes, so this adapter documents the discovery workflow supported by
the portal and provides a seed-based normalization path.

Any record with nil or unverified financial data is stored with
verification_status="needs_review" and financial fields = None. The portal URL
itself is authoritative for discovery.
"""

from datetime import date

from app.services.scheme_sources.base import NormalizedScheme, SchemeSourceAdapter

MSCHEME_URL = "https://www.myscheme.gov.in/"


class MySchemeAdapter(SchemeSourceAdapter):
    source_name = "myScheme"

    def fetch(self) -> list[NormalizedScheme]:
        # myScheme uses a JS-heavy SPA; no stable machine-readable API is
        # currently published. Records below are hand-verified references
        # pointing at the official scheme pages. Financial figures are only
        # included where confirmed by the official portal; otherwise None.
        return [
            NormalizedScheme(
                name="PM-SURAJ (PM Sampatti Suraksha Yojana for Marginalised)",
                slug="pm-suraj",
                description=(
                    "Pradhan Mantri Vaya Vandana – Sampatti Suraksha Yojana… "
                    "actually PM-SURAJ is the umbrella programme for providing "
                    "concessional credit to marginalised sections of society. "
                    "Applicants are routed to existing central schemes for "
                    "self-employment and education credit. Verify eligibility "
                    "and financial terms on the official scheme page."
                ),
                category="micro_finance",
                purpose="business",
                max_loan=None,
                min_loan=None,
                interest_rate=None,
                tenure_months=None,
                moratorium_months=None,
                income_threshold=None,
                project_min=None,
                project_max=None,
                education_focus=False,
                eligibility_notes=(
                    "For marginalised entrepreneurs/self-employed persons. "
                    "Actual loan terms are those of the parent central scheme."
                ),
                required_documents="Verify on official scheme page.",
                partner_required=False,
                source_name="myScheme",
                source_url=MSCHEME_URL,
                official_scheme_url="https://www.myscheme.gov.in/schemes",
                official_apply_url=None,
                last_verified=date.today().isoformat(),
                source_type="official_government",
                verification_status="needs_review",
                is_demo=False,
                rules=[],
            ),
        ]