from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {}
pool_kwargs = {}

if is_sqlite:
    connect_args["check_same_thread"] = False
else:
    # Fail fast when the database is unreachable at cold start instead of
    # hanging until the serverless function limit. sslmode is passed straight
    # through from the DSN (Neon uses ?sslmode=require).
    connect_args["connect_timeout"] = 10
    pool_kwargs.update({
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    })

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **pool_kwargs,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    # Self-heal: if startup provisioning was skipped because the database was
    # temporarily unreachable, retry on database use until it succeeds (the
    # in-process _ready flag stops retrying after the first success).
    from app.db.init_db import ensure_ready

    ensure_ready()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
