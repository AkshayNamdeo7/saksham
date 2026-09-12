"""
Regression test for the production Neon schema migration.

The live Neon `schemes` table predates the current SQLAlchemy models and is
missing newly-added columns (confirmed by
`psycopg2.errors.UndefinedColumn: column schemes.short_name does not exist`
on a serverless cold start). Base.metadata.create_all() does not add missing
columns to an existing table, so we verify the idempotent runtime migration:

- an "old" schema (missing the canonical official-source columns) is migrated;
- missing columns are added with the correct types;
- existing rows, ids and slugs are preserved (nothing dropped/duplicated);
- ORM queries against the migrated table work (no UndefinedColumn);
- running the migration a second time is a no-op.

PostgreSQL column-type accuracy is asserted by compiling the ADD COLUMN DDL
with the postgresql dialect (without requiring a live Postgres server).
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from sqlalchemy.orm import Session

from app.db.migrate import build_add_column_sql, migrate_schema
from app.models import Scheme


def _legacy_scheme_columns():
    return [
        Column("id", Integer, primary_key=True),
        Column("name", String(200), nullable=False),
        Column("slug", String(200), unique=True, nullable=False),
        Column("description", Text, nullable=False),
        Column("category", String(100), nullable=False),
        Column("purpose", String(100), nullable=False),
        Column("max_loan", Float, nullable=False),
        Column("min_loan", Float, nullable=False),
        Column("interest_rate", Float, nullable=True),
        Column("tenure_months", Integer, nullable=False),
        Column("moratorium_months", Integer, nullable=False),
        Column("income_threshold", Float, nullable=True),
        Column("project_min", Float, nullable=True),
        Column("project_max", Float, nullable=True),
        Column("education_focus", Boolean, nullable=False),
        Column("eligibility_notes", Text, nullable=False),
        Column("required_documents", Text, nullable=False),
        Column("partner_required", Boolean, nullable=False),
        Column("active", Boolean, nullable=False),
        Column("is_demo", Boolean, nullable=False),
        Column("official", Boolean, nullable=False),
        Column("source_type", String(50), nullable=False),
        Column("verification_status", String(50), nullable=False),
        Column("created_at", DateTime, nullable=True),
        Column("updated_at", DateTime, nullable=True),
    ]

NEW_CANONICAL_COLUMNS = {
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
    "data_confidence",
    "is_loan",
    "source_name",
    "source_url",
    "official_scheme_url",
    "official_apply_url",
    "last_verified",
}

LEGACY_ROW_ID = 10


@pytest.fixture()
def old_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path.as_posix()}/old_saksham.db"
    )
    meta = MetaData()
    Table("schemes", meta, *_legacy_scheme_columns())
    meta.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            meta.tables["schemes"].insert().values(
                id=LEGACY_ROW_ID,
                name="Legacy Official Scheme",
                slug="legacy-official",
                description="pre-migration record",
                category="term_loan",
                purpose="business",
                max_loan=500000.0,
                min_loan=10000.0,
                interest_rate=9.0,
                tenure_months=60,
                moratorium_months=3,
                income_threshold=500000.0,
                project_min=None,
                project_max=None,
                education_focus=False,
                eligibility_notes="",
                required_documents="",
                partner_required=True,
                active=True,
                is_demo=False,
                official=True,
                source_type="official_government",
                verification_status="verified",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
    yield engine
    engine.dispose()


def _column_names(engine, table="schemes"):
    from sqlalchemy import inspect as sa_inspect

    return {c["name"] for c in sa_inspect(engine).get_columns(table)}


def test_migration_adds_missing_columns_and_preserves_rows(old_engine):
    assert "short_name" not in _column_names(old_engine)

    added = migrate_schema(old_engine)

    columns = _column_names(old_engine)
    for c in NEW_CANONICAL_COLUMNS:
        assert c in columns, f"{c} missing after migration"
    assert {"short_name"} <= columns
    assert {a.split(".")[-1] for a in added} <= columns

    # Existing rows, ids and slugs are untouched.
    with Session(bind=old_engine) as s:
        scheme = s.query(Scheme).filter_by(slug="legacy-official").one()
        assert scheme.id == LEGACY_ROW_ID
        assert scheme.name == "Legacy Official Scheme"
        assert scheme.short_name is None  # new column, null for existing rows
        assert scheme.active is True
        assert scheme.official is True

        # Official-scheme bootstrap query works after migration.
        assert (
            s.query(Scheme)
            .filter(Scheme.official.is_(True), Scheme.active.is_(True))
            .count()
            == 1
        )
        assert s.query(Scheme).count() == 1


def test_migration_is_idempotent_and_never_duplicates(old_engine):
    first = migrate_schema(old_engine)
    assert first

    columns_before = _column_names(old_engine)
    second = migrate_schema(old_engine)
    assert second == []

    assert _column_names(old_engine) == columns_before
    with Session(bind=old_engine) as s:
        assert s.query(Scheme).count() == 1
        assert s.query(Scheme).filter_by(slug="legacy-official").count() == 1


def test_postgresql_ddl_types_match_models():
    pg = pg_dialect()
    scheme_table = Scheme.__table__

    assert (
        build_add_column_sql("schemes", scheme_table.c.short_name, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "short_name" VARCHAR(200)'
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.target_groups, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "target_groups" JSON'
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.age_min, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "age_min" INTEGER'
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.interest_tiers, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "interest_tiers" JSON'
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.source_type, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "source_type" VARCHAR(50) '
        "NOT NULL DEFAULT 'demo'"
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.verification_status, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "verification_status" VARCHAR(50) '
        "NOT NULL DEFAULT 'demo'"
    )
    assert "NOT NULL DEFAULT" not in build_add_column_sql(
        "schemes", scheme_table.c.official, pg
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.is_loan, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "is_loan" BOOLEAN DEFAULT true'
    )
    assert (
        build_add_column_sql("schemes", scheme_table.c.official, pg)
        == 'ALTER TABLE "schemes" ADD COLUMN IF NOT EXISTS "official" BOOLEAN DEFAULT false'
    )