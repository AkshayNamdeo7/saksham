"""
Idempotent runtime schema migration for existing tables.

Base.metadata.create_all() only creates missing TABLES. When a table already
exists in an older shape (for example the production Neon schema predates the
current SQLAlchemy models), missing COLUMNS are not added automatically and the
first ORM entity query fails with psycopg2.errors.UndefinedColumn.

This module diffs every model table against the live schema using
sqlalchemy.inspect() and issues safe, idempotent ALTER TABLE ADD COLUMN
statements for the columns the application currently requires. It never drops
anything and never touches existing rows or existing columns, and it is safe to
run repeatedly (and from concurrent serverless instances).

Column-type accuracy comes from the SQLAlchemy model definitions themselves:
each DDL is compiled with the active dialect so String/Text/Integer/Float/
Boolean/JSON/DateTime map to the correct backend types.
"""

import logging
from typing import Sequence

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text

from app.db.session import Base, engine as default_engine

logger = logging.getLogger("saksham.migrate")


def _default_literal(column, dialect):
    """Render a plain-SQL DEFAULT literal for a column, or None if none is safe.

    Prefers the Python default when it is a scalar (not a callable), falling
    back to an explicit server_default. JSON/DateTime defaults have no portable
    literal processor and return None.
    """
    server_default = column.server_default
    if server_default is not None:
        arg = server_default.arg
        if hasattr(arg, "text"):  # sqlalchemy TextClause — use verbatim
            return str(arg.text)
        return str(arg)

    default = column.default
    if default is not None:
        arg = default.arg
        if callable(arg):  # e.g. datetime.utcnow() default — no scalar literal
            return None
        lit = column.type.literal_processor(dialect)
        if lit is not None:
            try:
                return lit(arg)
            except Exception:
                return None
    return None


def build_add_column_sql(table_name: str, column, dialect) -> str:
    """Return the ALTER TABLE ADD COLUMN statement for a single column.

    The statement targets the exact PostgreSQL type compiled from the model
    definition. New columns stay NULL for existing rows when the model has no
    default; when the model defines a scalar default the DEFAULT clause is
    emitted too so pre-existing rows receive the model's documented baseline
    (and non-optional response fields like is_loan never read as NULL).
    """
    col_type = column.type.compile(dialect=dialect)
    default_sql = _default_literal(column, dialect)
    dialect_name = dialect.name

    if dialect_name == "postgresql":
        stmt = f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{column.name}" {col_type}'
    else:
        stmt = f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {col_type}'

    if not column.nullable and default_sql is not None:
        return f"{stmt} NOT NULL DEFAULT {default_sql}"
    if not column.nullable:
        # No safe default: adding NOT NULL would make existing rows invalid.
        logger.warning(
            "No safe default for non-nullable %s.%s — adding column as nullable; "
            "new rows must set it explicitly",
            table_name,
            column.name,
        )
        return stmt
    if default_sql is not None:
        # A nullable column with a model default still needs the DEFAULT clause
        # so pre-existing rows are backfilled with the model's documented
        # baseline instead of being left NULL (NULL would violate non-optional
        # response fields such as is_loan / official and break the API).
        return f"{stmt} DEFAULT {default_sql}"
    return stmt


def _is_duplicate_column(exc_text: str, dialect_name: str) -> bool:
    low = exc_text.lower()
    if dialect_name == "postgresql":
        return "duplicate column" in low
    return "duplicate column name" in low


def migrate_schema(engine=None) -> Sequence[str]:
    """Add any model columns missing from existing tables. Idempotent.

    Returns the list of \"table.column\" entries added on this run (empty on a
    no-op re-run). Raises on unexpected failures so the caller can log the
    technical reason server-side; the app never crashes (see
    app.db.init_db.provision_on_startup).
    """
    engine = engine or default_engine
    dialect = engine.dialect
    dialect_name = dialect.name
    added = []

    for table in Base.metadata.sorted_tables:
        insp = sa_inspect(engine)
        if not insp.has_table(table.name):
            # create_all creates missing tables; nothing to migrate.
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            stmt = build_add_column_sql(table.name, column, dialect)
            try:
                with engine.begin() as conn:
                    conn.execute(text(stmt))
            except Exception as exc:
                # A concurrent serverless instance may have already added it
                # between our inspect and the ALTER — treat that as success.
                if _is_duplicate_column(str(exc), dialect_name):
                    logger.info("Column already added concurrently: %s.%s", table.name, column.name)
                    continue
                raise
            added.append(f"{table.name}.{column.name}")
            logger.info(
                "Added missing column %s (%s) to table %s",
                column.name,
                column.type.compile(dialect=dialect),
                table.name,
            )

    if added:
        logger.info("Schema migration completed: added %d missing column(s).", len(added))
    return added