"""
Government-of-India official scheme sources.

These are the primary target-group finance/credit programmes relevant to the
Saksham problem statement. Records are hand-verified against the official
agency websites. Missing/uncertain financial values are stored as None and
flagged verification_status="needs_review" — Saksham never invents figures.
"""

from datetime import date

from app.services.scheme_sources.base import NormalizedScheme, SchemeSourceAdapter

NSFDC_URL = "https://nsfdc.gov.in/"
NBCFDC_URL = "https://ncbcfdc.gov.in/"
NSKFDC_URL = "https://nskfdc.nic.in/"
SJE_URL = "https://socialjustice.gov.in/"


class GovernmentSourcesAdapter(SchemeSourceAdapter):
    source_name = "Government of India"

    def fetch(self) -> list[NormalizedScheme]:
        today = date.today().isoformat()
        return [
            NormalizedScheme(
                name="NSFDC Loan Scheme for Scheduled Castes (Micro/Marginal Enterprise)",
                slug="nsfdc-scheme",
                description=(
                    "Concessional finance for Scheduled Caste entrepreneurs to set "
                    "up or expand micro/small income-generating activities through "
                    "State Chanelling Agencies (SCAs). Terms are fixed by the "
                    "NSFDC and its partner SCAs; confirm current amounts and "
                    "interest on the official pages."
                ),
                category="micro_finance",
                purpose="business",
                max_loan=300000,
                min_loan=50000,
                interest_rate=None,
                tenure_months=None,
                moratorium_months=None,
                income_threshold=300000,
                project_min=None,
                project_max=None,
                education_focus=False,
                eligibility_notes=(
                    "Applicant must belong to a Scheduled Caste family with annual "
                    "family income within the prevailing ceiling. Loan terms are "
                    "set by NSFDC/SCA guidelines."
                ),
                required_documents=(
                    "Identity, caste certificate, income certificate, and project "
                    "proposal — verify the full list on the official page."
                ),
                partner_required=True,
                source_name="NSFDC",
                source_url=NSFDC_URL,
                official_scheme_url=NSFDC_URL,
                official_apply_url=None,
                last_verified=today,
                source_type="official_government",
                verification_status="needs_review",
                is_demo=False,
                rules=[
                    ("purpose", "business", "Business/self-employment purpose"),
                    ("category", "micro_finance", "Micro-finance category"),
                ],
            ),
            NormalizedScheme(
                name="NBCFDC Concessional Loan for Backward Classes (Self-Employment)",
                slug="nbcfdc-scheme",
                description=(
                    "Concessional finance for entrepreneurs belonging to OBC / "
                    "Non-creamy-layer Backward Classes for setting up "
                    "self-employment ventures through State Chanelling Agencies. "
                    "Amounts and subsidy rates are prescribed by NBCFDC."
                ),
                category="micro_finance",
                purpose="self_employment",
                max_loan=100000,
                min_loan=20000,
                interest_rate=None,
                tenure_months=None,
                moratorium_months=None,
                income_threshold=250000,
                project_min=None,
                project_max=None,
                education_focus=False,
                eligibility_notes=(
                    "Applicant belongs to a Backward Class, is over 18, and the "
                    "annual family income is within the prevailing ceiling."
                ),
                required_documents=(
                    "Identity, caste (OBC) certificate, income certificate, project "
                    "proposal — verify the full list on the official page."
                ),
                partner_required=True,
                source_name="NBCFDC",
                source_url=NBCFDC_URL,
                official_scheme_url=NBCFDC_URL,
                official_apply_url=None,
                last_verified=today,
                source_type="official_government",
                verification_status="needs_review",
                is_demo=False,
                rules=[
                    ("purpose", "self_employment", "Self-employment purpose"),
                    ("category", "micro_finance", "Micro-finance category"),
                ],
            ),
            NormalizedScheme(
                name="NSKFDC (National Safai Karamcharis Finance & Development Corporation) Concessional Finance",
                slug="nskfdc-scheme",
                description=(
                    "Concessional credit and financial assistance for persons "
                    "engaged in / dependent on sanitation-related activities to set "
                    "up income-generation units. Distributed via SCAs and public "
                    "sector banks."
                ),
                category="micro_finance",
                purpose="self_employment",
                max_loan=None,
                min_loan=None,
                interest_rate=None,
                tenure_months=None,
                moratorium_months=None,
                income_threshold=300000,
                project_min=None,
                project_max=None,
                education_focus=False,
                eligibility_notes=(
                    "Persons engaged in or dependent on sanitation-related "
                    "livelihood; income ceiling applies per NSKFDC norms."
                ),
                required_documents="Verify on the official NSKFDC portal.",
                partner_required=True,
                source_name="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                official_apply_url=None,
                last_verified=today,
                source_type="official_government",
                verification_status="needs_review",
                is_demo=False,
                rules=[
                    ("purpose", "self_employment", "Self-employment purpose"),
                    ("category", "micro_finance", "Micro-finance category"),
                ],
            ),
            NormalizedScheme(
                name="Central Sector Scheme for Educational Loan (Ministry of Social Justice & Empowerment)",
                slug="sj-edu-loan",
                description=(
                    "Interest subsidy on higher-education loans for eligible "
                    "students from SC and other notified categories. The "
                    "underlying loan is availed from a bank; the subsidy is "
                    "provided by the Ministry."
                ),
                category="education",
                purpose="education",
                max_loan=None,
                min_loan=None,
                interest_rate=None,
                tenure_months=None,
                moratorium_months=None,
                income_threshold=400000,
                project_min=None,
                project_max=None,
                education_focus=True,
                eligibility_notes=(
                    "Full interest subsidy on the education loan during the study "
                    "period for eligible SC/central-sector students. Annual family "
                    "income ceiling applies. Confirm on official page."
                ),
                required_documents="Verify on the official Ministry page.",
                partner_required=False,
                source_name="Ministry of Social Justice & Empowerment",
                source_url=SJE_URL,
                official_scheme_url=SJE_URL,
                official_apply_url=None,
                last_verified=today,
                source_type="official_government",
                verification_status="needs_review",
                is_demo=False,
                rules=[
                    ("purpose", "education", "Education purpose"),
                    ("category", "education", "Education category"),
                ],
            ),
        ]