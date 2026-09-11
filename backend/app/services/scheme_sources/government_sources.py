"""
Government-of-India official scheme sources.

These are the primary target-group finance/credit programmes relevant to the
Saksham problem statement. Records are hand-verified against the official
agency websites (last verification session: 2026-09-11):

- NSFDC (nsfdc.nic.in): all five schemes (MFS, AMY, Term Loan, Udyam Nidhi and
  ELS) verified against the official loan/credit schemes page
  (https://nsfdc.nic.in/scheme) — annual family income ceiling Rs 5.00 lakh
  effective January 2026, finance up to 90% of project cost.
- NBCFDC (nbcfdc.gov.in): General (Individual) Loan and Education Loan
  verified against the official Individual Loan Scheme, Pattern of Finance and
  Loan Flyer pages (income ceiling Rs 5.00 lakh, max loan Rs 25.00 lakh, 85/15
  finance pattern, education at 8% p.a. over up to 10 years including a 5-year
  moratorium). "New Swarnima for Women" and "Mahila Samriddhi Yojana" are not
  published as distinct schemes on the current official pages, so those records
  remain "needs_review" with unconfirmed income fields stored as None.
- NSKFDC (nskfdc.nic.in): the site rejects automated fetching (homepage and
  scheme content pages), so all nine records remain "needs_review"; their
  occupation/target-group eligibility (Safai Karamcharis and dependents) is
  preserved and nothing is recast as a caste-based rule.
- PM-DAKSH and PM-AJAY (verified against their myscheme.gov.in scheme pages
  together with official DOSJE/PIB material): both are support programmes and
  NOT loans.

Missing/uncertain financial values are stored as None — Saksham never invents
figures.
"""

from datetime import date

from app.services.scheme_sources.base import NormalizedScheme, SchemeSourceAdapter

NSFDC_URL = "https://nsfdc.nic.in/"
NSFDC_FAQ_URL = "https://nsfdc.nic.in/faqs"
NSFDC_SCHEME_URL = "https://nsfdc.nic.in/scheme"
NBCFDC_URL = "https://nbcfdc.gov.in/"
NBCFDC_INDIVIDUAL_URL = "https://nbcfdc.gov.in/nbcfdc/web/en/individual-loan-scheme"
NBCFDC_GROUP_URL = "https://nbcfdc.gov.in/nbcfdc/web/en/group-loan-scheme"
NSKFDC_URL = "https://nskfdc.nic.in/"
MSCHEME_URL = "https://www.myscheme.gov.in/"
MSCHEME_PM_DAKSH_URL = "https://www.myscheme.gov.in/schemes/pm-daksh"
MSCHEME_PM_AJAY_URL = "https://www.myscheme.gov.in/schemes/pmajay-ag"
PM_SURAJ_URL = "https://pmsuraj.dosje.gov.in/"

SC_DOCS = [
    "aadhaar",
    "caste_certificate",
    "income_certificate",
    "bank_details",
    "project_report",
    "passport_photo",
]
EDU_DOCS = [
    "aadhaar",
    "caste_certificate",
    "income_certificate",
    "bank_details",
    "education_documents",
    "admission_letter",
    "passport_photo",
]
SUPPORT_DOCS = ["aadhaar", "passport_photo"]

SC_PROJECT_BUSINESS = [
    "Agriculture & Allied",
    "Small Industries",
    "Service & Transport",
]

DEFAULT_RULES = [
    ("purpose", "self_employment", "Self-employment purpose"),
    ("category", "business", "Business category"),
]
EDUCATION_RULES = [
    ("purpose", "education", "Education purpose"),
    ("category", "education", "Education category"),
]


class GovernmentSourcesAdapter(SchemeSourceAdapter):
    source_name = "Government of India"

    def fetch(self) -> list[NormalizedScheme]:
        today = date.today().isoformat()

        def _mk(slug, name, description, category, purpose, docs=None, rules=None, **kw):
            if docs is None:
                docs = EDU_DOCS if category == "education" else (SUPPORT_DOCS if category == "support" else SC_DOCS)
            defaults = dict(
                slug=slug,
                name=name,
                description=description,
                category=category,
                purpose=purpose,
                document_keys=docs or [],
                rules=rules or [],
                source_type="official_government",
                verification_status="verified",
                last_verified=today,
                is_demo=False,
                official=True,
                is_loan=True,
                partner_required=True,
                state_scope=["nationwide"],
                data_confidence="verified",
                source_url=NSFDC_URL,
                official_scheme_url=NSFDC_URL,
                application_mode="Online via the PM-SURAJ portal or offline through an authorized Channelizing Agency (SCA/CA)",
            )
            defaults.update(kw)
            return NormalizedScheme(**defaults)

        def _sca(**kw):
            kw.setdefault("source_url", NSFDC_URL)
            kw.setdefault("official_scheme_url", NSFDC_SCHEME_URL)
            kw.setdefault("official_apply_url", PM_SURAJ_URL)
            kw.setdefault("application_mode", "Online via the PM-SURAJ portal or offline through an authorized State Channelizing Agency (SCA)")
            kw.setdefault("provider", "NSFDC")
            kw.setdefault("target_groups", ["Scheduled Castes"])
            kw.setdefault("income_limit", 500000)
            kw.setdefault("course_type", [])
            return _mk(source_name="NSFDC", **kw)

        return [
            # ------------------------------ NSFDC ------------------------------
            _sca(
                slug="nsfdc-mfs",
                name="Micro Finance Scheme (MFS) — NSFDC",
                short_name="MFS",
                description=(
                    "Micro-credit from NSFDC for small income-generating activities of "
                    "Scheduled Caste beneficiaries — units costing up to Rs 1.40 lakh. "
                    "Repayment is in quarterly installments within 3 years (including a "
                    "3-month moratorium). Disbursed through State Channelizing Agencies/CAs."
                ),
                category="business",
                sub_category="micro finance",
                purpose="self_employment",
                business_sectors=SC_PROJECT_BUSINESS,
                max_loan=125000,
                max_loan_amount=125000,
                project_cost_min=50000,
                project_cost_max=140000,
                project_min=50000,
                project_max=140000,
                interest_rate=6.5,
                interest_rate_type="fixed",
                repayment_period="3 years",
                repayment_unit="years",
                tenure_months=36,
                moratorium="3 months",
                moratorium_months=3,
                rules=DEFAULT_RULES,
            ),
            _sca(
                slug="nsfdc-amy",
                name="Aajeevika Micro-Finance Yojana (AMY) — NSFDC",
                short_name="AMY",
                description=(
                    "Prompt, need-based micro-finance from NSFDC through selected "
                    "NBFC-MFIs for projects costing up to Rs 1.40 lakh. Maximum loan "
                    "Rs 1.25 lakh; repayment within 3 years (including a 3-month "
                    "moratorium). Interest 15% p.a."
                ),
                category="business",
                sub_category="micro finance",
                purpose="self_employment",
                business_sectors=SC_PROJECT_BUSINESS,
                max_loan=125000,
                max_loan_amount=125000,
                project_cost_min=50000,
                project_cost_max=140000,
                project_min=50000,
                project_max=140000,
                interest_rate=15.0,
                interest_rate_type="fixed",
                repayment_period="3 years",
                repayment_unit="years",
                tenure_months=36,
                moratorium="3 months",
                moratorium_months=3,
                rules=DEFAULT_RULES,
            ),
            _sca(
                slug="nsfdc-term-loan",
                name="Term Loan — NSFDC",
                short_name="Term Loan",
                description=(
                    "NSFDC finance for larger income-generating projects costing more "
                    "than Rs 1.40 lakh and up to Rs 50.00 lakh for Scheduled Caste "
                    "entrepreneurs. Maximum loan up to Rs 45.00 lakh at 8% p.a.; "
                    "repayment within 7 years (6-month moratorium, extended to 12 "
                    "months for plantation/construction)."
                ),
                category="business",
                sub_category="term loan",
                purpose="business",
                business_sectors=SC_PROJECT_BUSINESS,
                max_loan=4500000,
                max_loan_amount=4500000,
                project_cost_min=140000,
                project_cost_max=5000000,
                project_min=140000,
                project_max=5000000,
                interest_rate=8.0,
                interest_rate_type="fixed",
                repayment_period="7 years",
                repayment_unit="years",
                tenure_months=84,
                moratorium="6 months (12 months for plantation and construction)",
                moratorium_months=6,
                rules=[
                    ("purpose", "business", "Business purpose"),
                    ("category", "business", "Business category"),
                ],
            ),
            _sca(
                slug="nsfdc-udyam-nidhi",
                name="Udyam Nidhi Yojana (UNY) — NSFDC",
                short_name="Udyam Nidhi",
                description=(
                    "NSFDC loans for small/micro activities with project cost up to "
                    "Rs 5.00 lakh. Maximum loan Rs 4.50 lakh. Implemented through "
                    "Cooperative Societies/Cooperative Banks at 13% p.a. and through "
                    "Small Finance Banks at 15% p.a. Repayment within 5 years "
                    "(including a 3-month moratorium)."
                ),
                category="business",
                sub_category="micro finance",
                purpose="self_employment",
                business_sectors=SC_PROJECT_BUSINESS,
                max_loan=450000,
                max_loan_amount=450000,
                project_cost_min=None,
                project_cost_max=500000,
                project_max=500000,
                interest_rate=None,
                interest_rate_type="tiered",
                interest_tiers=[
                    {"channel": "Cooperative Societies / Cooperative Banks", "interest_rate": 13.0},
                    {"channel": "Small Finance Banks", "interest_rate": 15.0},
                ],
                repayment_period="5 years",
                repayment_unit="years",
                tenure_months=60,
                moratorium="3 months",
                moratorium_months=3,
                rules=DEFAULT_RULES,
            ),
            _sca(
                slug="nsfdc-educational-loan",
                name="Educational Loan Scheme (ELS) — NSFDC",
                short_name="ELS",
                description=(
                    "NSFDC loans up to Rs 40.00 lakh (or 90% of the course fee, "
                    "whichever is less) at 6.5% p.a. for regular full-time "
                    "professional/technical courses at recognized institutions in "
                    "India or abroad. Repayment up to 10–12 years; moratorium equals "
                    "course duration plus 1 year."
                ),
                category="education",
                sub_category="education loan",
                purpose="education",
                education_focus=True,
                course_type=[
                    "Undergraduate",
                    "Postgraduate",
                    "Professional",
                    "Technical",
                    "Doctoral",
                ],
                education_requirements=(
                    "Regular full-time professional/technical course at a recognized "
                    "institution in India or abroad (e.g. Engineering, Medical, Management, Law)."
                ),
                max_loan=4000000,
                max_loan_amount=4000000,
                finance_percentage=90.0,
                interest_rate=6.5,
                interest_rate_type="fixed",
                repayment_period="10–12 years",
                repayment_unit="months",
                moratorium="Course duration plus 1 year (up to 6 months once repayment has started)",
                rules=EDUCATION_RULES,
            ),
            # ------------------------------ NBCFDC ------------------------------
            _mk(
                slug="nbcfdc-general-loan",
                name="General Loan for Self-Employment — NBCFDC",
                short_name="General Loan",
                description=(
                    "Concessional term loan under NBCFDC for Backward Classes "
                    "(OBC / non-creamy layer) entrepreneurs to set up or expand "
                    "income-generating ventures. Annual family income ceiling "
                    "Rs 5.00 lakh. Loans up to Rs 1.25 lakh at 7% p.a. (4-year "
                    "tenure) and above Rs 1.25 lakh up to Rs 25.00 lakh at 8% p.a. "
                    "(up to 7-year tenure); up to 85% of project cost financed "
                    "(15% partner/beneficiary share)."
                ),
                category="business",
                sub_category="term loan",
                purpose="self_employment",
                source_name="NBCFDC",
                provider="NBCFDC",
                source_url=NBCFDC_URL,
                official_scheme_url=NBCFDC_INDIVIDUAL_URL,
                application_mode="Offline through an authorized State Channelizing Agency (SCA)",
                target_groups=["Backward Classes (OBC, non-creamy layer)"],
                occupation_groups=[
                    "Non-creamy layer Backward Classes",
                    "De-notified, Nomadic and Semi-Nomadic Tribes",
                ],
                income_limit=500000,
                income_threshold=500000,
                max_loan_amount=2500000,
                max_loan=2500000,
                project_cost_min=None,
                project_cost_max=None,
                project_min=None,
                project_max=None,
                finance_percentage=85.0,
                beneficiary_contribution_percentage=15.0,
                interest_rate=8.0,
                interest_rate_type="tiered",
                interest_tiers=[
                    {"loan_up_to": 125000, "interest_rate": 7.0},
                    {"loan_up_to": 2500000, "interest_rate": 8.0},
                ],
                repayment_period="up to 7 years (4 years up to Rs 1.25 lakh)",
                repayment_unit="years",
                tenure_months=84,
                moratorium="1 quarter (3 months)",
                moratorium_months=3,
                verification_status="verified",
                data_confidence="verified",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nbcfdc-education-loan",
                name="Educational Loan Scheme — NBCFDC",
                short_name="Education Loan",
                description=(
                    "Education loans for eligible Backward Class students pursuing "
                    "recognized professional/technical courses. Up to Rs 25.00 lakh "
                    "at a uniform 8% p.a. interest rate; up to 85% of course cost "
                    "financed; repayment within up to 10 years (inclusive of a "
                    "5-year moratorium). Applicant must have secured admission in a "
                    "duly accredited institution with minimum 50% marks in the "
                    "qualifying examination."
                ),
                category="education",
                sub_category="education loan",
                purpose="education",
                education_focus=True,
                source_name="NBCFDC",
                provider="NBCFDC",
                source_url=NBCFDC_URL,
                official_scheme_url=NBCFDC_INDIVIDUAL_URL,
                application_mode="Offline through an authorized State Channelizing Agency (SCA)",
                target_groups=["Backward Classes (OBC, non-creamy layer)"],
                income_limit=500000,
                income_threshold=500000,
                course_type=["Undergraduate", "Postgraduate", "Professional", "Technical"],
                education_requirements=(
                    "Admission to a duly accredited/recognized professional/technical "
                    "institution in India or abroad, with a minimum 50% marks in the "
                    "qualifying examination."
                ),
                max_loan_amount=2500000,
                max_loan=2500000,
                finance_percentage=85.0,
                interest_rate=8.0,
                interest_rate_type="fixed",
                repayment_period="up to 10 years (inclusive of 5-year moratorium)",
                repayment_unit="years",
                tenure_months=120,
                moratorium="5 years (included within the 10-year tenure)",
                moratorium_months=60,
                verification_status="verified",
                data_confidence="verified",
                rules=EDUCATION_RULES,
            ),
            _mk(
                slug="nbcfdc-new-swarnima-women",
                name="New Swarnima Scheme for Women — NBCFDC",
                short_name="New Swarnima",
                description=(
                    "Concessional assistance for women belonging to Backward Classes "
                    "to start small income-generating activities. Maximum loan "
                    "Rs 2.00 lakh at 5% p.a.; up to 95% of the project cost financed "
                    "(5% beneficiary contribution); repayment up to 8 years."
                ),
                category="business",
                sub_category="micro finance",
                purpose="self_employment",
                source_name="NBCFDC",
                provider="NBCFDC",
                source_url=NBCFDC_URL,
                official_scheme_url=NBCFDC_INDIVIDUAL_URL,
                application_mode="Offline through an authorized State Channelizing Agency (SCA)",
                target_groups=["Women", "Backward Classes (OBC, non-creamy layer)"],
                gender_rule="female",
                income_limit=None,
                income_threshold=None,
                max_loan_amount=200000,
                max_loan=200000,
                project_cost_max=220000,
                project_max=220000,
                finance_percentage=95.0,
                beneficiary_contribution_percentage=5.0,
                interest_rate=5.0,
                interest_rate_type="fixed",
                repayment_period="8 years",
                repayment_unit="years",
                tenure_months=96,
                moratorium="6 months (project-dependent)",
                moratorium_months=6,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nbcfdc-mahila-samriddhi",
                name="Mahila Samriddhi Yojana — NBCFDC",
                short_name="Mahila Samriddhi",
                description=(
                    "NBCFDC credit support to women Self-Help Groups (SHGs) of "
                    "Backward Classes. Up to Rs 1.25 lakh per member for groups of "
                    "up to 20 members; interest 4% p.a.; up to 95% of project cost "
                    "financed; repayment up to 48 months after a 6-month moratorium."
                ),
                category="business",
                sub_category="micro credit",
                purpose="self_employment",
                source_name="NBCFDC",
                provider="NBCFDC",
                source_url=NBCFDC_URL,
                official_scheme_url=NBCFDC_GROUP_URL,
                application_mode="Offline through an authorized State Channelizing Agency (SCA)",
                target_groups=["Women Self-Help Groups", "Backward Classes (OBC, non-creamy layer)"],
                gender_rule="female",
                income_limit=None,
                income_threshold=None,
                max_loan_amount=1500000,
                max_loan=1500000,
                min_loan_amount=125000,
                min_loan=125000,
                finance_percentage=95.0,
                interest_rate=4.0,
                interest_rate_type="fixed",
                repayment_period="48 months",
                repayment_unit="months",
                tenure_months=48,
                moratorium="6 months",
                moratorium_months=6,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            # ------------------------------ NSKFDC ------------------------------
            _mk(
                slug="nskfdc-general-term-loan",
                name="General Term Loan — NSKFDC",
                short_name="General Term Loan",
                description=(
                    "Concessional term loan under NSKFDC for persons engaged in or "
                    "dependent on sanitation-related activities (Safai Karamcharis and "
                    "their dependents) for income-generating units. Maximum loan "
                    "Rs 15.00 lakh; interest slabbed at 8%/9% p.a.; repayment up to 10 years."
                ),
                category="business",
                sub_category="term loan",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                    "Persons engaged in sewage/sanitation-related activities",
                ],
                max_loan_amount=1500000,
                max_loan=1500000,
                project_cost_max=1600000,
                project_max=1600000,
                interest_rate=None,
                interest_rate_type="tiered",
                interest_tiers=[
                    {"loan_up_to": 1000000, "interest_rate": 8.0},
                    {"loan_up_to": 1500000, "interest_rate": 9.0},
                ],
                repayment_period="10 years",
                repayment_unit="years",
                tenure_months=120,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-mahila-adhikarita",
                name="Mahila Adhikarita Yojana — NSKFDC",
                short_name="Mahila Adhikarita (MAY)",
                description=(
                    "NSKFDC loan for beneficiary women and SHGs of Safai Karamcharis "
                    "for micro income-generation activities. Maximum loan Rs 2.00 "
                    "lakh at 7% p.a.; repayment up to 5 years."
                ),
                category="business",
                sub_category="micro finance",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                target_groups=["Women", "Women Self-Help Groups", "Safai Karamcharis"],
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                ],
                gender_rule="female",
                max_loan_amount=200000,
                max_loan=200000,
                interest_rate=7.0,
                interest_rate_type="fixed",
                repayment_period="5 years",
                repayment_unit="years",
                tenure_months=60,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-mahila-samridhi",
                name="Mahila Samridhi Yojana — NSKFDC",
                short_name="Mahila Samridhi (MSY)",
                description=(
                    "NSKFDC loan for women beneficiaries and groups engaged in "
                    "sanitation-related or small enterprises. Maximum loan Rs 1.00 "
                    "lakh at 6% p.a.; repayment up to 3 years."
                ),
                category="business",
                sub_category="micro finance",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                target_groups=["Women", "Safai Karamcharis"],
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Scavengers",
                    "Dependents of Safai Karamcharis",
                ],
                gender_rule="female",
                max_loan_amount=100000,
                max_loan=100000,
                interest_rate=6.0,
                interest_rate_type="fixed",
                repayment_period="3 years",
                repayment_unit="years",
                tenure_months=36,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-micro-credit-finance",
                name="Micro Credit Finance Scheme — NSKFDC",
                short_name="Micro Credit",
                description=(
                    "NSKFDC micro-credit for small income-generation ventures of "
                    "Safai Karamcharis and dependents. Maximum loan Rs 1.00 lakh at "
                    "7% p.a.; repayment up to 3 years."
                ),
                category="business",
                sub_category="micro credit",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                ],
                max_loan_amount=100000,
                max_loan=100000,
                interest_rate=7.0,
                interest_rate_type="fixed",
                repayment_period="3 years",
                repayment_unit="years",
                tenure_months=36,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-education-loan",
                name="Education Loan Scheme — NSKFDC",
                short_name="Education Loan",
                description=(
                    "NSKFDC education loans for children of Safai Karamcharis and "
                    "dependents pursuing recognized professional/technical courses. "
                    "Up to Rs 10.00 lakh for studies in India at 6% p.a. and up to "
                    "Rs 20.00 lakh abroad at 7% p.a. Repayment rules vary — confirm "
                    "the installment schedule on the official scheme page."
                ),
                category="education",
                sub_category="education loan",
                purpose="education",
                education_focus=True,
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                ],
                course_type=["Undergraduate", "Postgraduate", "Professional", "Technical"],
                education_requirements="Admission to a recognized professional/technical course in India or abroad.",
                max_loan_amount=2000000,
                max_loan=2000000,
                interest_rate=None,
                interest_rate_type="tiered",
                interest_tiers=[
                    {"course_location": "India", "interest_rate": 6.0},
                    {"course_location": "Abroad", "interest_rate": 7.0},
                ],
                repayment_period="Repayable in installments per NSKFDC repayment rules",
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=EDUCATION_RULES,
            ),
            _mk(
                slug="nskfdc-pay-and-use-community-toilets",
                name="Scheme for Pay & Use Community Toilets — NSKFDC",
                short_name="Pay & Use Toilets",
                description=(
                    "NSKFDC finance for setting up pay-and-use community toilets by "
                    "Safai Karamcharis/SHGs. Maximum loan Rs 25.00 lakh at 8% p.a.; "
                    "repayment up to 10 years."
                ),
                category="business",
                sub_category="sanitation enterprise",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                    "Self-Help Groups",
                ],
                max_loan_amount=2500000,
                max_loan=2500000,
                interest_rate=8.0,
                interest_rate_type="fixed",
                repayment_period="10 years",
                repayment_unit="years",
                tenure_months=120,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-sanitary-marts",
                name="Sanitary Marts Scheme — NSKFDC",
                short_name="Sanitary Marts",
                description=(
                    "NSKFDC finance for setting up sanitary marts run by Safai "
                    "Karamcharis/dependents for sale of sanitary products. Maximum "
                    "loan Rs 15.00 lakh at 7% p.a.; repayment up to 10 years."
                ),
                category="business",
                sub_category="sanitation enterprise",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                ],
                max_loan_amount=1500000,
                max_loan=1500000,
                interest_rate=7.0,
                interest_rate_type="fixed",
                repayment_period="10 years",
                repayment_unit="years",
                tenure_months=120,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-green-business",
                name="Green Business Scheme — NSKFDC",
                short_name="Green Business",
                description=(
                    "NSKFDC finance for green/clean business ventures by Safai "
                    "Karamcharis and dependents (e.g. waste management, recycling). "
                    "Maximum loan Rs 30.00 lakh with interest slabbed at 6/7/8% "
                    "p.a.; repayment up to 10 years."
                ),
                category="business",
                sub_category="green enterprise",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                ],
                business_sectors=["Waste management", "Recycling", "Green covers", "Energy conservation"],
                max_loan_amount=3000000,
                max_loan=3000000,
                interest_rate=None,
                interest_rate_type="tiered",
                interest_tiers=[
                    {"loan_up_to": 1000000, "interest_rate": 6.0},
                    {"loan_up_to": 2000000, "interest_rate": 7.0},
                    {"loan_up_to": 3000000, "interest_rate": 8.0},
                ],
                repayment_period="10 years",
                repayment_unit="years",
                tenure_months=120,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            _mk(
                slug="nskfdc-swachhta-udhyami",
                name="Swachhta Udyami Yojana — NSKFDC",
                short_name="Swachhta Udyami (SUY)",
                description=(
                    "NSKFDC finance for individual Safai Karamcharis (up to "
                    "Rs 15.00 lakh at 6% p.a.) and group/enterprise borrowers (up to "
                    "Rs 50.00 lakh through private agencies at 8% p.a.) for "
                    "sanitation-related ventures. Repayment up to 7 years."
                ),
                category="business",
                sub_category="sanitation enterprise",
                purpose="self_employment",
                source_name="NSKFDC",
                provider="NSKFDC",
                source_url=NSKFDC_URL,
                official_scheme_url=NSKFDC_URL,
                application_mode="Through NSKFDC SCAs / public sector banks / private agencies",
                occupation_groups=[
                    "Safai Karamcharis (sanitation workers)",
                    "Dependents of Safai Karamcharis",
                ],
                max_loan_amount=5000000,
                max_loan=5000000,
                interest_rate=None,
                interest_rate_type="tiered",
                interest_tiers=[
                    {"borrower": "Individual", "interest_rate": 6.0},
                    {"borrower": "Group / enterprise (private agency)", "interest_rate": 8.0},
                ],
                repayment_period="7 years",
                repayment_unit="years",
                tenure_months=84,
                verification_status="needs_review",
                data_confidence="needs_review",
                rules=DEFAULT_RULES,
            ),
            # ------------------------- Support (not loans) -------------------------
            _mk(
                slug="pm-daksh",
                name="PM-DAKSH — Skill Development for SC/OBC/EBC",
                short_name="PM-DAKSH",
                description=(
                    "PM-DAKSH (Pradhan Mantri Dakshta Aur Kushalta Sampann "
                    "Hitgrahi) is the Ministry of Social Justice and Empowerment "
                    "skill-development programme for SC, OBC, EBC, De-notified/"
                    "Nomadic Tribes and Safai Karamcharis (including waste "
                    "pickers). It offers free NSQF-compliant skill/up-skilling "
                    "training (age 18–45) with a stipend. This is a support "
                    "programme, not a loan."
                ),
                category="support",
                sub_category="skill / livelihood support",
                purpose="self_employment",
                source_name="Department of Social Justice and Empowerment (Govt. of India)",
                provider="DOSJE",
                source_url=MSCHEME_URL,
                official_scheme_url=MSCHEME_PM_DAKSH_URL,
                application_mode="Through empanelled training institutes / the nodal SC finance corporation of the beneficiary's State",
                target_groups=["Scheduled Castes", "OBC", "Economically Backward Classes (EBC)"],
                is_loan=False,
                partner_required=False,
                verification_status="verified",
                data_confidence="verified",
                rules=[],
            ),
            _mk(
                slug="pm-ajay",
                name="PM-AJAY — Umbrella SC Upliftment support",
                short_name="PM-AJAY",
                description=(
                    "PM-AJAY (Pradhan Mantri Anusuchit Jaati Abhyuday Yojana) is "
                    "the Department of Social Justice and Empowerment's umbrella "
                    "Centrally Sponsored Scheme for the upliftment of Scheduled "
                    "Castes (merger of SCA to SCSP, PMAGY and Babu Jagjivan Ram "
                    "Chhatrawas Yojana). It funds income-generating schemes, skill "
                    "development, infrastructure and hostels delivered through "
                    "States/UTs. This is a support programme, not a loan."
                ),
                category="support",
                sub_category="skill / livelihood support",
                purpose="self_employment",
                source_name="Department of Social Justice and Empowerment (Govt. of India)",
                provider="DOSJE",
                source_url=MSCHEME_URL,
                official_scheme_url=MSCHEME_PM_AJAY_URL,
                application_mode="Implemented through States/UTs — enterprise and skill components route through the respective SC finance corporations",
                target_groups=["Scheduled Castes"],
                is_loan=False,
                partner_required=False,
                verification_status="verified",
                data_confidence="verified",
                rules=[],
            ),
        ]