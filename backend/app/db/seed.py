"""
Seed the database with realistic DEMO data.

Every scheme and partner row is marked is_demo=True. Values are prototype
figures derived from the hackathon problem statement and are NOT official.
"""

import json

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import Base, engine, SessionLocal
from app.models import (
    AdminUser,
    AuditEvent,
    Document,
    Partner,
    Scheme,
    SchemeRule,
)

IND = lambda n: f"{n:,.0f}"

SCHEMES = [
    {
        "name": "Micro Finance Scheme",
        "slug": "micro-finance-scheme",
        "category": "micro_finance",
        "purpose": "business",
        "description": (
            "Demo concessional micro-credit for small income-generating activities such as "
            "dairy, petty trade, and handicrafts. Suitable for first-time borrowers with a "
            "small project footprint."
        ),
        "max_loan": 140000,
        "min_loan": 10000,
        "interest_rate": 4.0,
        "tenure_months": 36,
        "moratorium_months": 3,
        "income_threshold": 250000,
        "project_min": 10000,
        "project_max": 160000,
        "education_focus": False,
        "eligibility_notes": (
            "Demo: applicant belongs to an eligible marginalized/SC category, small project "
            "size, concessional rate. Subject to official guidelines."
        ),
        "required_documents": "Aadhaar, caste certificate, income certificate, project brief",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "business", "Loan purpose"),
            ("category", "micro_finance", "Scheme category"),
            ("max_loan", "140000", "Demo ceiling"),
        ],
    },
    {
        "name": "Self-Employment Assistance Scheme",
        "slug": "self-employment-assistance",
        "category": "micro_finance",
        "purpose": "self_employment",
        "description": (
            "Demo subsidy-linked assistance for self-employment ventures — tailoring units, "
            "repair shops, and service micro-enterprises."
        ),
        "max_loan": 100000,
        "min_loan": 5000,
        "interest_rate": 4.0,
        "tenure_months": 36,
        "moratorium_months": 3,
        "income_threshold": 250000,
        "project_min": 5000,
        "project_max": 120000,
        "education_focus": False,
        "eligibility_notes": "Demo: self-employment project, income threshold applies.",
        "required_documents": "Aadhaar, caste certificate, income certificate, project plan",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "self_employment", "Loan purpose"),
            ("category", "micro_finance", "Scheme category"),
        ],
    },
    {
        "name": "Term Loan Scheme",
        "slug": "term-loan-scheme",
        "category": "term_loan",
        "purpose": "business",
        "description": (
            "Demo term loan for larger business expansion — machinery, capacity building, and "
            "working capital for growing micro-enterprises."
        ),
        "max_loan": 5000000,
        "min_loan": 500000,
        "interest_rate": 6.0,
        "tenure_months": 60,
        "moratorium_months": 6,
        "income_threshold": None,
        "project_min": 500000,
        "project_max": 5500000,
        "education_focus": False,
        "eligibility_notes": (
            "Demo: established or well-researched business plan, larger project size."
        ),
        "required_documents": "Aadhaar, caste certificate, income certificate, project report, bank statements",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "business", "Loan purpose"),
            ("category", "term_loan", "Scheme category"),
        ],
    },
    {
        "name": "Educational Loan Scheme",
        "slug": "educational-loan-scheme",
        "category": "education",
        "purpose": "education",
        "description": (
            "Demo concessional education loan for undergraduate, postgraduate and professional "
            "courses at recognized institutions."
        ),
        "max_loan": 1000000,
        "min_loan": 50000,
        "interest_rate": 4.0,
        "tenure_months": 84,
        "moratorium_months": 12,
        "income_threshold": 400000,
        "project_min": None,
        "project_max": None,
        "education_focus": True,
        "eligibility_notes": (
            "Demo: admission at a recognized institution, family income threshold applies."
        ),
        "required_documents": "Aadhaar, caste certificate, income certificate, admission proof, fee structure",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("course_level", "UG/PG/professional", "Course level"),
            ("category", "education", "Scheme category"),
        ],
    },
    {
        "name": "Women Entrepreneurship Loan",
        "slug": "women-entrepreneurship-loan",
        "category": "micro_finance",
        "purpose": "business",
        "description": (
            "Demo micro-credit designed for women-led micro-enterprises including tailoring, "
            "food processing, and small retail."
        ),
        "max_loan": 200000,
        "min_loan": 20000,
        "interest_rate": 4.0,
        "tenure_months": 48,
        "moratorium_months": 3,
        "income_threshold": 300000,
        "project_min": 20000,
        "project_max": 220000,
        "education_focus": False,
        "eligibility_notes": "Demo: women-led micro-enterprise, demo income threshold.",
        "required_documents": "Aadhaar, caste certificate, income certificate, project plan",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "business", "Loan purpose"),
            ("category", "micro_finance", "Scheme category"),
        ],
    },
    {
        "name": "Agri-Allied Business Scheme",
        "slug": "agri-allied-business-scheme",
        "category": "term_loan",
        "purpose": "business",
        "description": (
            "Demo support for agriculture-allied ventures — dairy, poultry, fisheries, and "
            "food processing micro-units."
        ),
        "max_loan": 3000000,
        "min_loan": 100000,
        "interest_rate": 5.0,
        "tenure_months": 60,
        "moratorium_months": 6,
        "income_threshold": 500000,
        "project_min": 100000,
        "project_max": 3200000,
        "education_focus": False,
        "eligibility_notes": "Demo: agri-allied project, verification required.",
        "required_documents": "Aadhaar, caste certificate, land/unit proof, project report",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "business", "Loan purpose"),
            ("category", "term_loan", "Scheme category"),
        ],
    },
    {
        "name": "Skill-to-Enterprise Loan",
        "slug": "skill-to-enterprise-loan",
        "category": "micro_finance",
        "purpose": "self_employment",
        "description": (
            "Demo bridge loan for trained vocational graduates to convert skills into "
            "self-employment income."
        ),
        "max_loan": 80000,
        "min_loan": 10000,
        "interest_rate": 4.0,
        "tenure_months": 36,
        "moratorium_months": 3,
        "income_threshold": 250000,
        "project_min": 10000,
        "project_max": 90000,
        "education_focus": False,
        "eligibility_notes": "Demo: requires skill training certificate.",
        "required_documents": "Aadhaar, caste certificate, income certificate, skill certificate",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "self_employment", "Loan purpose"),
            ("category", "micro_finance", "Scheme category"),
            ("skill_cert", "true", "Skill certificate required"),
        ],
    },
    {
        "name": "Startup Support Scheme",
        "slug": "startup-support-scheme",
        "category": "term_loan",
        "purpose": "business",
        "description": (
            "Demo startup-financing support for technology-enabled and services micro-"
            "startups founded by eligible beneficiaries."
        ),
        "max_loan": 2000000,
        "min_loan": 200000,
        "interest_rate": 5.0,
        "tenure_months": 60,
        "moratorium_months": 9,
        "income_threshold": 600000,
        "project_min": 200000,
        "project_max": 2200000,
        "education_focus": False,
        "eligibility_notes": "Demo: business plan with startup intent, verification required.",
        "required_documents": "Aadhaar, caste certificate, income certificate, business plan",
        "partner_required": True,
        "active": True,
        "is_demo": True,
        "rules": [
            ("purpose", "business", "Loan purpose"),
            ("category", "term_loan", "Scheme category"),
        ],
    },
]

DOCUMENTS = [
    {
        "key": "aadhaar",
        "name": "Aadhaar / Identity Proof",
        "name_hi": "आधार / पहचान प्रमाण",
        "description": "Verify identity. Required for most financial assistance.",
        "is_required": True,
        "applies_to": "all",
    },
    {
        "key": "caste_certificate",
        "name": "Caste Certificate",
        "name_hi": "जाति प्रमाण पत्र",
        "description": "Establishes eligibility under SC/eligible category provisions.",
        "is_required": True,
        "applies_to": "all",
    },
    {
        "key": "income_certificate",
        "name": "Income Certificate",
        "name_hi": "आय प्रमाण पत्र",
        "description": "Used to check the applicable demo income threshold.",
        "is_required": True,
        "applies_to": "all",
    },
    {
        "key": "bank_details",
        "name": "Bank Account Details",
        "name_hi": "बैंक खाता विवरण",
        "description": "For disbursal and repayment tracking.",
        "is_required": True,
        "applies_to": "all",
    },
    {
        "key": "project_report",
        "name": "Project Report / Business Plan",
        "name_hi": "परियोजना रिपोर्ट / व्यवसाय योजना",
        "description": "Outlines the venture, cost, and expected income.",
        "is_required": False,
        "applies_to": "business",
    },
    {
        "key": "quotation",
        "name": "Quotations / Estimates",
        "name_hi": "कोटेशन / अनुमान",
        "description": "For asset-based lending, evidence of cost.",
        "is_required": False,
        "applies_to": "business",
    },
    {
        "key": "education_documents",
        "name": "Education Documents",
        "name_hi": "शैक्षणिक दस्तावेज़",
        "description": "Marksheets, certificates for course eligibility.",
        "is_required": False,
        "applies_to": "education",
    },
    {
        "key": "admission_letter",
        "name": "Admission Letter & Fee Structure",
        "name_hi": "प्रवेश पत्र और शुल्क संरचना",
        "description": "Proof of admission and course fees.",
        "is_required": True,
        "applies_to": "education",
    },
    {
        "key": "passport_photo",
        "name": "Passport-size Photographs",
        "name_hi": "पासपोर्ट साइज़ फोटो",
        "description": "For application forms.",
        "is_required": True,
        "applies_to": "all",
    },
    {
        "key": "skill_certificate",
        "name": "Skill Training Certificate",
        "name_hi": "कौशल प्रशिक्षण प्रमाण पत्र",
        "description": "Where the scheme requires prior skill training.",
        "is_required": False,
        "applies_to": "business",
    },
]

# Demo partners across Madhya Pradesh, Maharashtra, UP, Rajasthan, Bihar
PARTNERS = [
    {
        "name": "MP State Backward Classes Finance & Development Corporation (Demo)",
        "type": "SCA",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "address": "Sadhana Bhavan, Shivaji Nagar, Bhopal",
        "lat": 23.2599,
        "lng": 77.4126,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "term-loan-scheme", "women-entrepreneurship-loan", "skill-to-enterprise-loan"],
    },
    {
        "name": "Central Bank of India – Bhopal Branch (Demo)",
        "type": "PSB",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "address": "Indira Press Complex, Zone-I, Bhopal",
        "lat": 23.2547,
        "lng": 77.4029,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme", "agri-allied-business-scheme", "startup-support-scheme"],
    },
    {
        "name": "Bank of India – Bhopal Main Branch (Demo)",
        "type": "PSB",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "address": "Hoshangabad Road, Bhopal",
        "lat": 23.2178,
        "lng": 77.4298,
        "schemes": ["micro-finance-scheme", "educational-loan-scheme", "term-loan-scheme"],
    },
    {
        "name": "Madhyanchal Gramin Bank – Bhopal (Demo)",
        "type": "RRB",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "address": "Berasia Road, Bhopal",
        "lat": 23.2955,
        "lng": 77.4891,
        "schemes": ["micro-finance-scheme", "agri-allied-business-scheme", "self-employment-assistance", "women-entrepreneurship-loan"],
    },
    {
        "name": "Bandhan Financial Services – Bhopal (Demo)",
        "type": "NBFC-MFI",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
        "city": "Bhopal",
        "address": "Kolar Road, Bhopal",
        "lat": 23.1551,
        "lng": 77.4212,
        "schemes": ["micro-finance-scheme", "women-entrepreneurship-loan", "skill-to-enterprise-loan"],
    },
    {
        "name": "MP State Minorities Finance (Demo)",
        "type": "SCA",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "city": "Indore",
        "address": "Race Course Road, Indore",
        "lat": 22.7196,
        "lng": 75.8577,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "term-loan-scheme", "educational-loan-scheme"],
    },
    {
        "name": "Bank of Baroda – Indore (Demo)",
        "type": "PSB",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "city": "Indore",
        "address": "MG Road, Indore",
        "lat": 22.7196,
        "lng": 75.8577,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme", "startup-support-scheme"],
    },
    {
        "name": "Narmada Jhabua Gramin Bank – Indore (Demo)",
        "type": "RRB",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "city": "Indore",
        "address": "AB Road, Indore",
        "lat": 22.7079,
        "lng": 75.8785,
        "schemes": ["micro-finance-scheme", "agri-allied-business-scheme"],
    },
    {
        "name": "Ujjivan Small Finance – Indore (Demo)",
        "type": "NBFC-MFI",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "city": "Indore",
        "address": "Vijay Nagar, Indore",
        "lat": 22.7386,
        "lng": 75.8957,
        "schemes": ["women-entrepreneurship-loan", "micro-finance-scheme", "skill-to-enterprise-loan"],
    },
    {
        "name": "MP Backward Classes – Jabalpur (Demo)",
        "type": "SCA",
        "state": "Madhya Pradesh",
        "district": "Jabalpur",
        "city": "Jabalpur",
        "address": "Civil Lines, Jabalpur",
        "lat": 23.1815,
        "lng": 79.9864,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "women-entrepreneurship-loan"],
    },
    {
        "name": "Punjab National Bank – Gwalior (Demo)",
        "type": "PSB",
        "state": "Madhya Pradesh",
        "district": "Gwalior",
        "city": "Gwalior",
        "address": "Lashkar, Gwalior",
        "lat": 26.2183,
        "lng": 78.1828,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme"],
    },
    {
        "name": "Maharashtra Backward Class Development Corp (Demo)",
        "type": "SCA",
        "state": "Maharashtra",
        "district": "Mumbai",
        "city": "Mumbai",
        "address": "Churchgate, Mumbai",
        "lat": 18.9387,
        "lng": 72.8262,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "term-loan-scheme"],
    },
    {
        "name": "State Bank of India – Dadar (Demo)",
        "type": "PSB",
        "state": "Maharashtra",
        "district": "Mumbai",
        "city": "Mumbai",
        "address": "Dadar West, Mumbai",
        "lat": 19.0176,
        "lng": 72.8446,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme", "startup-support-scheme"],
    },
    {
        "name": "Maharashtra Gramin Bank – Nagpur (Demo)",
        "type": "RRB",
        "state": "Maharashtra",
        "district": "Nagpur",
        "city": "Nagpur",
        "address": "Civil Lines, Nagpur",
        "lat": 21.1458,
        "lng": 79.0882,
        "schemes": ["micro-finance-scheme", "agri-allied-business-scheme", "women-entrepreneurship-loan"],
    },
    {
        "name": "UP Backward Classes Finance Dev Corp (Demo)",
        "type": "SCA",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "city": "Lucknow",
        "address": "Vibhuti Khand, Gomti Nagar, Lucknow",
        "lat": 26.8467,
        "lng": 80.9462,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "term-loan-scheme", "educational-loan-scheme"],
    },
    {
        "name": "Punjab & Sind Bank – Lucknow (Demo)",
        "type": "PSB",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "city": "Lucknow",
        "address": "Hazratganj, Lucknow",
        "lat": 26.8496,
        "lng": 80.9477,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme"],
    },
    {
        "name": "Aryavart Gramin Bank – Lucknow (Demo)",
        "type": "RRB",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "city": "Lucknow",
        "address": "Aliganj, Lucknow",
        "lat": 26.8837,
        "lng": 80.9477,
        "schemes": ["agri-allied-business-scheme", "micro-finance-scheme", "self-employment-assistance"],
    },
    {
        "name": "Bihar State Backward Classes Finance (Demo)",
        "type": "SCA",
        "state": "Bihar",
        "district": "Patna",
        "city": "Patna",
        "address": "Bailey Road, Patna",
        "lat": 25.5941,
        "lng": 85.1376,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "women-entrepreneurship-loan"],
    },
    {
        "name": "Central Bank of India – Patna (Demo)",
        "type": "PSB",
        "state": "Bihar",
        "district": "Patna",
        "city": "Patna",
        "address": "West Gandhi Maidan, Patna",
        "lat": 25.6071,
        "lng": 85.1394,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme"],
    },
    {
        "name": "Dakshin Bihar Gramin Bank – Patna (Demo)",
        "type": "RRB",
        "state": "Bihar",
        "district": "Patna",
        "city": "Patna",
        "address": "Danapur, Patna",
        "lat": 25.6254,
        "lng": 85.0394,
        "schemes": ["agri-allied-business-scheme", "micro-finance-scheme"],
    },
    {
        "name": "Rajasthan SC/ST Finance & Dev Corp (Demo)",
        "type": "SCA",
        "state": "Rajasthan",
        "district": "Jaipur",
        "city": "Jaipur",
        "address": "Pant Krishi Bhawan, Jaipur",
        "lat": 26.9124,
        "lng": 75.7873,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "term-loan-scheme"],
    },
    {
        "name": "Baroda Rajasthan Kshetriya Gramin Bank (Demo)",
        "type": "RRB",
        "state": "Rajasthan",
        "district": "Jaipur",
        "city": "Jaipur",
        "address": "Ajmer Road, Jaipur",
        "lat": 26.9,
        "lng": 75.78,
        "schemes": ["micro-finance-scheme", "agri-allied-business-scheme", "women-entrepreneurship-loan"],
    },
    {
        "name": "Haryana Backward Classes Finance Dev Corp (Demo)",
        "type": "SCA",
        "state": "Haryana",
        "district": "Chandigarh",
        "city": "Chandigarh",
        "address": "Sector 17-C, Chandigarh",
        "lat": 30.7333,
        "lng": 76.7794,
        "schemes": ["micro-finance-scheme", "self-employment-assistance", "startup-support-scheme"],
    },
    {
        "name": "Canara Bank – Chandigarh (Demo)",
        "type": "PSB",
        "state": "Haryana",
        "district": "Chandigarh",
        "city": "Chandigarh",
        "address": "Sector 17-B, Chandigarh",
        "lat": 30.7333,
        "lng": 76.7794,
        "schemes": ["micro-finance-scheme", "term-loan-scheme", "educational-loan-scheme"],
    },
    {
        "name": "Bihar Gram Jyoti Self Help Group Finance (Demo)",
        "type": "NBFC-MFI",
        "state": "Bihar",
        "district": "Gaya",
        "city": "Gaya",
        "address": "Station Road, Gaya",
        "lat": 24.7955,
        "lng": 84.9994,
        "schemes": ["women-entrepreneurship-loan", "micro-finance-scheme", "skill-to-enterprise-loan"],
    },
]

SCHEME_TO_DOCS = {
    "micro-finance-scheme": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "project_report", "passport_photo"],
    "self-employment-assistance": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "project_report", "passport_photo"],
    "term-loan-scheme": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "project_report", "quotation"],
    "educational-loan-scheme": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "admission_letter", "education_documents", "passport_photo"],
    "women-entrepreneurship-loan": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "project_report", "passport_photo"],
    "agri-allied-business-scheme": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "project_report", "quotation"],
    "skill-to-enterprise-loan": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "skill_certificate", "project_report"],
    "startup-support-scheme": ["aadhaar", "caste_certificate", "income_certificate", "bank_details", "project_report", "passport_photo"],
}

PARTNER_STATUS = [
    ("accepting", 90, 60.0, "low"),
    ("limited", 55, 78.0, "low"),
    ("unavailable", 0, 92.0, "medium"),
    ("accepting", 85, 45.0, "low"),
    ("accepting", 95, 35.0, "low"),
    ("limited", 60, 80.0, "low"),
    ("accepting", 88, 50.0, "low"),
    ("accepting", 92, 30.0, "low"),
    ("limited", 50, 85.0, "medium"),
    ("accepting", 90, 40.0, "low"),
    ("accepting", 85, 55.0, "low"),
    ("accepting", 93, 25.0, "low"),
    ("limited", 58, 82.0, "medium"),
    ("accepting", 87, 48.0, "low"),
    ("accepting", 90, 38.0, "low"),
    ("accepting", 88, 52.0, "low"),
    ("limited", 62, 79.0, "medium"),
    ("accepting", 84, 40.0, "low"),
    ("accepting", 91, 33.0, "low"),
    ("accepting", 86, 49.0, "low"),
    ("limited", 57, 88.0, "medium"),
    ("accepting", 89, 42.0, "low"),
    ("accepting", 93, 28.0, "low"),
    ("accepting", 90, 36.0, "low"),
    ("accepting", 85, 44.0, "low"),
]


def seed(db: Session):
    # Documents
    doc_map = {}
    for d in DOCUMENTS:
        rec = (
            db.query(Document)
            .filter(Document.key == d["key"])
            .first()
        )
        if rec is None:
            rec = Document(**d)
            db.add(rec)
        else:
            for k, v in d.items():
                setattr(rec, k, v)
        db.flush()
        doc_map[d["key"]] = rec

    # Schemes
    scheme_map = {}
    for s in SCHEMES:
        rules = list(s.get("rules", []))
        payload = {k: v for k, v in s.items() if k != "rules"}
        rec = db.query(Scheme).filter(Scheme.slug == s["slug"]).first()
        if rec is None:
            rec = Scheme(**payload)
            db.add(rec)
        else:
            for k, v in payload.items():
                setattr(rec, k, v)
        db.flush()
        for old in list(rec.rules):
            db.delete(old)
        db.flush()
        for rkey, rval, rdesc in rules:
            rec.rules.append(
                SchemeRule(rule_key=rkey, rule_value=rval, description=rdesc)
            )
        # attach documents
        doc_keys = SCHEME_TO_DOCS.get(rec.slug, [])
        rec.documents = []
        for dk in doc_keys:
            if dk in doc_map:
                rec.documents.append(doc_map[dk])
        db.flush()
        scheme_map[rec.slug] = rec

    # Partners
    for idx, p in enumerate(PARTNERS):
        schemes = list(p.get("schemes", []))
        data = {k: v for k, v in p.items() if k != "schemes"}
        rec = (
            db.query(Partner)
            .filter(
                Partner.name == p["name"],
                Partner.state == p["state"],
                Partner.district == p["district"],
            )
            .first()
        )
        status, cap, fund, npa = PARTNER_STATUS[idx % len(PARTNER_STATUS)]
        data = dict(data)
        data["latitude"] = data.pop("lat")
        data["longitude"] = data.pop("lng")
        data.update(
            {
                "status": status,
                "capacity_pct": cap,
                "fund_utilization_pct": fund,
                "npa_indicator": npa,
                "accepting_applications": status == "accepting",
                "phone": f"+91-7{6000000000 + idx * 137:010d}"[:13],
                "email": f"demo.partner{idx+1}@saksham.example",
                "is_demo": True,
            }
        )
        if rec is None:
            rec = Partner(**data)
            db.add(rec)
        else:
            for k, v in data.items():
                setattr(rec, k, v)
        db.flush()
        rec.schemes = []
        db.flush()
        for slug in schemes:
            if slug in scheme_map:
                rec.schemes.append(scheme_map[slug])
        db.flush()

    # Admin user
    admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if admin is None:
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("saksham@2026"),
            display_name="Saksham Admin",
        )
        db.add(admin)
    else:
        admin.password_hash = hash_password("saksham@2026")

    # Audit marker
    db.add(AuditEvent(event_type="seed", payload=json.dumps({"demo": True})))
    db.commit()


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
        print("Database seeded with demo data.")
    finally:
        db.close()


if __name__ == "__main__":
    run()