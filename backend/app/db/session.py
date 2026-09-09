from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {}
pool_kwargs = {}

if is_sqlite:
    connect_args["check_same_thread"] = False
else:
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
