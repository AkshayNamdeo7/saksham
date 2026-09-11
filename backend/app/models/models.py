from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Table,
)
from sqlalchemy.orm import relationship

from app.db.session import Base

scheme_partner_association = Table(
    "scheme_partner",
    Base.metadata,
    Column("scheme_id", Integer, ForeignKey("schemes.id"), primary_key=True),
    Column("partner_id", Integer, ForeignKey("partners.id"), primary_key=True),
)

scheme_document_association = Table(
    "scheme_document",
    Base.metadata,
    Column("scheme_id", Integer, ForeignKey("schemes.id"), primary_key=True),
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
)


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False, default="")
    category = Column(String(100), nullable=False)  # micro_finance / term_loan / education
    purpose = Column(String(100), nullable=False)  # business / self_employment / education
    max_loan = Column(Float, nullable=False, default=0)
    min_loan = Column(Float, nullable=False, default=0)
    interest_rate = Column(Float, nullable=True)
    tenure_months = Column(Integer, nullable=False, default=0)
    moratorium_months = Column(Integer, nullable=False, default=0)
    income_threshold = Column(Float, nullable=True)
    project_min = Column(Float, nullable=True)
    project_max = Column(Float, nullable=True)
    education_focus = Column(Boolean, default=False)
    eligibility_notes = Column(Text, nullable=False, default="")
    required_documents = Column(Text, nullable=False, default="")
    partner_required = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=True)
    # Canonical official-source fields (source of truth for the import)
    short_name = Column(String(200), nullable=True)
    provider = Column(String(200), nullable=True)
    sub_category = Column(String(100), nullable=True)
    target_groups = Column(JSON, nullable=True)
    occupation_groups = Column(JSON, nullable=True)
    gender_rule = Column(String(50), nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    income_limit = Column(Float, nullable=True)
    state_scope = Column(JSON, nullable=True)
    district_scope = Column(JSON, nullable=True)
    education_requirements = Column(String(200), nullable=True)
    course_type = Column(JSON, nullable=True)
    business_sectors = Column(JSON, nullable=True)
    project_cost_min = Column(Float, nullable=True)
    project_cost_max = Column(Float, nullable=True)
    min_loan_amount = Column(Float, nullable=True)
    max_loan_amount = Column(Float, nullable=True)
    finance_percentage = Column(Float, nullable=True)
    beneficiary_contribution_percentage = Column(Float, nullable=True)
    interest_rate_type = Column(String(50), nullable=True)
    interest_tiers = Column(JSON, nullable=True)
    moratorium = Column(String(100), nullable=True)
    repayment_period = Column(String(100), nullable=True)
    repayment_unit = Column(String(50), nullable=True)
    application_mode = Column(String(100), nullable=True)
    official = Column(Boolean, default=False)
    data_confidence = Column(String(50), nullable=True)
    is_loan = Column(Boolean, default=True)
    # Source metadata
    source_name = Column(String(200), nullable=True)
    source_url = Column(String(500), nullable=True)
    official_scheme_url = Column(String(500), nullable=True)
    official_apply_url = Column(String(500), nullable=True)
    last_verified = Column(String(50), nullable=True)
    source_type = Column(String(50), nullable=False, default="demo")  # official_government / demo
    verification_status = Column(String(50), nullable=False, default="demo")  # verified / demo / needs_review
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partners = relationship(
        "Partner",
        secondary=scheme_partner_association,
        back_populates="schemes",
    )
    documents = relationship(
        "Document",
        secondary=scheme_document_association,
        back_populates="schemes",
    )


class SchemeRule(Base):
    __tablename__ = "scheme_rules"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False, index=True)
    rule_key = Column(String(100), nullable=False)
    rule_value = Column(String(200), nullable=False)
    description = Column(String(255), nullable=False, default="")

    scheme = relationship("Scheme", backref="rules")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_hi = Column(String(200), nullable=True)
    description = Column(Text, nullable=False, default="")
    is_required = Column(Boolean, default=True)
    applies_to = Column(String(50), nullable=False, default="all")  # all/business/education

    schemes = relationship(
        "Scheme",
        secondary=scheme_document_association,
        back_populates="documents",
    )


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False)  # SCA / PSB / RRB / NBFC-MFI
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(Text, nullable=False, default="")
    latitude = Column(Float, nullable=False, default=0)
    longitude = Column(Float, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="accepting")  # accepting/limited/unavailable
    capacity_pct = Column(Integer, default=100)
    fund_utilization_pct = Column(Float, default=0)
    npa_indicator = Column(String(50), default="low")
    phone = Column(String(30), nullable=False, default="")
    email = Column(String(120), nullable=True)
    accepting_applications = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    schemes = relationship(
        "Scheme",
        secondary=scheme_partner_association,
        back_populates="partners",
    )


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"

    id = Column(Integer, primary_key=True, index=True)
    # user-provided profile (kept minimal, not sensitive)
    age = Column(Integer, nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    annual_family_income = Column(Float, nullable=True)
    purpose = Column(String(50), nullable=True)
    project_type = Column(String(100), nullable=True)
    project_cost = Column(Float, nullable=True)
    education_level = Column(String(100), nullable=True)
    course_type = Column(String(100), nullable=True)
    requested_loan = Column(Float, nullable=True)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    eligibility_check_id = Column(Integer, ForeignKey("eligibility_checks.id"), nullable=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    match_score = Column(Float, nullable=False, default=0)
    eligibility_status = Column(String(50), nullable=False, default="eligible")
    matched_criteria = Column(Text, nullable=True)
    unmatched_criteria = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    reasons = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scheme = relationship("Scheme")
    eligibility_check = relationship("EligibilityCheck")


class LoanCalculation(Base):
    __tablename__ = "loan_calculations"

    id = Column(Integer, primary_key=True, index=True)
    principal = Column(Float, nullable=False)
    annual_rate = Column(Float, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    moratorium_months = Column(Integer, default=0)
    emi = Column(Float, nullable=False)
    total_interest = Column(Float, nullable=False)
    total_repayment = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApplicationGuidance(Base):
    __tablename__ = "application_guidances"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    recommended_partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    loan_required = Column(Float, nullable=True)
    partner_score = Column(Float, nullable=True)
    guidance_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scheme = relationship("Scheme")
    recommended_partner = relationship("Partner")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(200), nullable=False, default="")
    role = Column(String(50), default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
