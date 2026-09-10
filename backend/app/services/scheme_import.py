"""
Import normalized official scheme records into the database.

This service is safe to run on every startup (idempotent upsert by slug).
It merges verified official records without deleting demo data.
"""

from sqlalchemy.orm import Session

from app.models import Document, Scheme, SchemeRule
from app.services.scheme_sources import (
    GovernmentSourcesAdapter,
    MySchemeAdapter,
    SchemeSourceAdapter,
    NormalizedScheme,
)


def _upsert_scheme(db: Session, rec: NormalizedScheme):
    scheme = db.query(Scheme).filter(Scheme.slug == rec.slug).first()
    if scheme is None:
        scheme = Scheme(slug=rec.slug, name=rec.name)
        db.add(scheme)
    scheme.name = rec.description
    scheme.name = rec.name
    scheme.description = rec.description
    scheme.category = rec.category
    scheme.purpose = rec.purpose
    # Only write financial values that are actually verified.
    scheme.max_loan = rec.max_loan or 0
    scheme.min_loan = rec.min_loan or 0
    scheme.interest_rate = rec.interest_rate or 0
    scheme.tenure_months = rec.tenure_months or 0
    scheme.moratorium_months = rec.moratorium_months or 0
    scheme.income_threshold = rec.income_threshold
    scheme.project_min = rec.project_min
    scheme.project_max = rec.project_max
    scheme.education_focus = rec.education_focus
    scheme.eligibility_notes = rec.eligibility_notes
    scheme.required_documents = rec.required_documents
    scheme.partner_required = rec.partner_required
    scheme.active = True

    # Source metadata
    scheme.source_name = rec.source_name
    scheme.source_url = rec.source_url
    scheme.official_scheme_url = rec.official_scheme_url
    scheme.official_apply_url = rec.official_apply_url
    scheme.last_verified = rec.last_verified
    scheme.source_type = rec.source_type
    scheme.verification_status = rec.verification_status
    scheme.is_demo = rec.is_demo

    db.flush()

    # Replace rules
    for old in list(scheme.rules):
        db.delete(old)
    db.flush()
    for rkey, rval, rdesc in rec.rules:
        scheme.rules.append(
            SchemeRule(rule_key=rkey, rule_value=rval, description=rdesc)
        )
    db.flush()

    # Attach matching documents by key
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