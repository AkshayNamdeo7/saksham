"""
Centralized, idempotent database provisioning for the Saksham API.

Schema creation (Base.metadata.create_all) and the official-data bootstrap must
still happen, but they must never take the whole API down during a serverless
cold start.

On Vercel every cold-start function instance runs the FastAPI startup hook. If
that hook opens a PostgreSQL connection that cannot be established in time
(e.g. a suspended Neon compute waking up, a transient network blip, a stale or
wrong endpoint) and lets the exception escape, every request on that instance
fails with "Application startup failed. Exiting.".

This module therefore:
- runs provisioning best-effort on startup (fast path when the DB is reachable),
- retries provisioning lazily on database requests until it succeeds when the
  startup attempt failed or was skipped (self-healing; retries stop after the
  first success in this process),
- never falls back to SQLite; DATABASE_URL stays required in app.core.config.
"""

import logging
import threading

logger = logging.getLogger("saksham.db")

_ready = False
_lock = threading.Lock()


def is_ready() -> bool:
    return _ready


def _provision() -> None:
    from app.core.config import settings
    from app.db.migrate import migrate_schema
    from app.db.seed import seed
    from app.db.session import Base, SessionLocal, engine
    from app.models import Scheme
    from app.services.scheme_import import import_official_schemes

    # Order matters:
    #   1. create missing tables
    #   2. add columns missing from existing (older) tables — BEFORE any ORM
    #      query touches the new model columns (fixes UndefinedColumn on a
    #      pre-migration Neon schema)
    #   3. then bootstrap data only if no official dataset exists
    Base.metadata.create_all(bind=engine)
    migrate_schema(engine)

    if not settings.SEED_ON_STARTUP:
        logger.info("Database schema ready; SEED_ON_STARTUP=0 skips data bootstrap.")
        return

    db = SessionLocal()
    try:
        # Bootstrap only when no active official scheme is present. Once the
        # official dataset exists (e.g. in Neon) it is left untouched; this
        # keeps cold starts fast and avoids re-importing on every invocation.
        has_official = (
            db.query(Scheme)
            .filter(Scheme.official.is_(True), Scheme.active.is_(True))
            .count()
            > 0
        )
        if not has_official:
            seed(db)
            import_official_schemes(db)
        elif (
            db.query(Scheme)
            .filter(
                Scheme.official.is_(True),
                Scheme.active.is_(True),
                Scheme.short_name.is_(None),
            )
            .count()
            > 0
        ):
            # Official rows predate the current model (schema migration just
            # added short_name + friends). The idempotent upsert backfills the
            # canonical fields for those rows without duplicating anything.
            logger.info("Refreshing legacy official rows with current canonical fields.")
            import_official_schemes(db)
        logger.info("Database provisioned (has_official=%s).", has_official)
    finally:
        db.close()


def ensure_ready() -> None:
    """Provision the database once per process success (thread-safe)."""
    global _ready
    if _ready:
        return
    with _lock:
        if _ready:
            return
        _provision()
        _ready = True


def provision_on_startup() -> None:
    """Best-effort provisioning during app startup. Never fatal."""
    try:
        ensure_ready()
    except Exception:
        logger.exception(
            "Database provisioning failed at startup; it will be retried on the "
            "first database request. Confirm DATABASE_URL points at Neon and is reachable."
        )