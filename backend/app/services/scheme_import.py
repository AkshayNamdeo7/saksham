"""
Import normalized official scheme records into the database.

This service is safe to run on every startup (idempotent upsert by slug).
It merges verified official records without deleting demo data: demo schemes
are kept as rows but de-activated, and legacy placeholder slugs are retired.
"""

import re

from sqlalchemy.orm import Session

from app.models import Document, Scheme, SchemeRule
from app.services.scheme_sources import (
    GovernmentSourcesAdapter,
    MySchemeAdapter,
    SchemeSourceAdapter,
    NormalizedScheme,
)

# Canonical official-source columns the importer copies from the normalized record.
CANONICAL_FIELDS = [
    "short_name",
    "provider",
    "sub_category",
    "target_groups",
    "occupation_groups",
    "gender_rule",
    "age_min",
    "age_max",
    "income_limit",
    "state_scope",
    "district_scope",
    "education_requirements",
    "course_type",
    "business_sectors",
    "project_cost_min",
    "project_cost_max",
    "min_loan_amount",
    "max_loan_amount",
    "finance_percentage",
    "beneficiary_contribution_percentage",
    "interest_rate_type",
    "interest_tiers",
    "moratorium",
    "repayment_period",
    "repayment_unit",
    "application_mode",
    "official",
    "data_confidence",
    "is_loan",
]

# Retired placeholder slugs from earlier prototype import runs.
LEGACY_OFFICIAL_SLUGS = {
    "nsfdc-scheme",
    "nbcfdc-scheme",
    "nskfdc-scheme",
    "sj-edu-loan",
    "pm-suraj",
}

DEFAULT_DOCS_NOTE = (
    "Additional documents may be required by the channelizing agency/partner."
)


def _months_from(text) -> int | None:
    """Extract an approximate month count from a human repayment string."""
    if not text:
        return None
    m = re.search(r"(\d+)\s*(months?|years?|yrs?)", str(text), re.IGNORECASE)
    if not m:
        return None
    num = int(m.group(1))
    return num * 12 if "year" in m.group(2).lower() else num


def _upsert_scheme(db: Session, rec: NormalizedScheme):
    scheme = db.query(Scheme).filter(Scheme.slug == rec.slug).first()
    if scheme is None:
        scheme = Scheme(slug=rec.slug, name=rec.name)
        db.add(scheme)
    scheme.name = rec.name
    scheme.description = rec.description
    scheme.category = rec.category
    scheme.purpose = rec.purpose
    scheme.eligibility_notes = rec.eligibility_notes
    scheme.partner_required = rec.partner_required
    scheme.active = True

    # Canonical official-source fields (single source of truth).
    for f in CANONICAL_FIELDS:
        setattr(scheme, f, getattr(rec, f))

    # Legacy columns — the recommendation engine and the frontend still read
    # these, so they are derived from the canonical fields when present.
    scheme.max_loan = (
        rec.max_loan_amount
        if rec.max_loan_amount is not None
        else (rec.max_loan or 0)
    )
    scheme.min_loan = (
        rec.min_loan_amount if rec.min_loan_amount is not None else (rec.min_loan or 0)
    )
    scheme.interest_rate = rec.interest_rate
    scheme.income_threshold = (
        rec.income_limit if rec.income_limit is not None else rec.income_threshold
    )
    scheme.project_min = (
        rec.project_cost_min if rec.project_cost_min is not None else rec.project_min
    )
    scheme.project_max = (
        rec.project_cost_max if rec.project_cost_max is not None else rec.project_max
    )
    scheme.education_focus = rec.education_focus
    scheme.tenure_months = rec.tenure_months or _months_from(rec.repayment_period) or 0
    scheme.moratorium_months = rec.moratorium_months or _months_from(rec.moratorium) or 0
    scheme.required_documents = rec.required_documents or DEFAULT_DOCS_NOTE

    # Source metadata.
    scheme.source_name = rec.source_name
    scheme.source_url = rec.source_url
    scheme.official_scheme_url = rec.official_scheme_url
    scheme.official_apply_url = rec.official_apply_url
    scheme.last_verified = rec.last_verified
    scheme.source_type = rec.source_type
    scheme.verification_status = rec.verification_status
    scheme.is_demo = rec.is_demo

    db.flush()

    # Replace rules.
    for old in list(scheme.rules):
        db.delete(old)
    db.flush()
    for rkey, rval, rdesc in rec.rules:
        scheme.rules.append(SchemeRule(rule_key=rkey, rule_value=rval, description=rdesc))
    db.flush()

    # Attach matching documents by key.
    doc_map = {d.key: d for d in db.query(Document).all()}
    attached = []
    for dk in rec.document_keys:
        if dk in doc_map:
            attached.append(doc_map[dk])
    if attached:
        scheme.documents = attached
    db.flush()
    return scheme


def import_official_schemes(db: Session, refresh: bool = False) -> dict:
    """Import all official-source records into the DB. Returns summary."""
    # Retire demo schemes and legacy placeholder slugs (rows are kept, not deleted).
    db.query(Scheme).filter(Scheme.is_demo.is_(True)).update(
        {Scheme.active: False}, synchronize_session=False
    )
    db.query(Scheme).filter(Scheme.slug.in_(LEGACY_OFFICIAL_SLUGS)).update(
        {Scheme.active: False}, synchronize_session=False
    )
    db.flush()

    adapters: list[SchemeSourceAdapter] = [
        MySchemeAdapter(),
        GovernmentSourcesAdapter(),
    ]
    stats = {"added": 0, "updated": 0, "skipped_invalid": 0, "schemes": []}
    for adapter in adapters:
        records = adapter.get_all(refresh=refresh)
        for rec in records:
            try:
                existing = db.query(Scheme).filter(Scheme.slug == rec.slug).first()
                prev_status = existing.verification_status if existing else None
                _upsert_scheme(db, rec)
                if existing is None:
                    stats["added"] += 1
                else:
                    stats["updated"] += 1
                stats["schemes"].append(
                    {
                        "slug": rec.slug,
                        "source_name": rec.source_name,
                        "verification_status": rec.verification_status,
                        "changed": existing is None or prev_status != rec.verification_status,
                    }
                )
            except Exception:
                stats["skipped_invalid"] += 1
                continue
    db.commit()
    return stats


def run():
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        stats = import_official_schemes(db)
        print(f"Official schemes imported: {stats['added']} added, {stats['updated']} updated.")
        for s in stats["schemes"]:
            print(f"  {s['slug']}: {s['source_name']} ({s['verification_status']})")
    finally:
        db.close()


if __name__ == "__main__":
    run()