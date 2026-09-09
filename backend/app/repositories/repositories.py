from sqlalchemy.orm import Session

from app.models import Scheme, Document, Partner
from app.schemas.schemas import SchemeCreate, SchemeUpdate, PartnerCreate, PartnerUpdate


class SchemeRepository:
    @staticmethod
    def list(db: Session, active_only: bool = False):
        q = db.query(Scheme)
        if active_only:
            q = q.filter(Scheme.active.is_(True))
        return q.all()

    @staticmethod
    def get(db: Session, scheme_id: int):
        return db.query(Scheme).filter(Scheme.id == scheme_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str):
        return db.query(Scheme).filter(Scheme.slug == slug).first()

    @staticmethod
    def create(db: Session, data: SchemeCreate):
        doc_keys = data.document_keys or []
        payload = data.model_dump(exclude={"document_keys"})
        scheme = Scheme(**payload)
        db.add(scheme)
        db.flush()
        _attach_documents(db, scheme, doc_keys)
        db.commit()
        db.refresh(scheme)
        return scheme

    @staticmethod
    def update(db: Session, scheme: Scheme, data: dict):
        for k, v in data.items():
            if k == "document_keys":
                continue
            if hasattr(scheme, k) and v is not None:
                setattr(scheme, k, v)
        if "document_keys" in data:
            _replace_documents(db, scheme, data["document_keys"] or [])
        db.commit()
        db.refresh(scheme)
        return scheme

    @staticmethod
    def delete(db: Session, scheme: Scheme):
        db.delete(scheme)
        db.commit()


def _attach_documents(db: Session, scheme: Scheme, keys: list[str]):
    docs = db.query(Document).filter(Document.key.in_(keys)).all()
    for d in docs:
        if d not in scheme.documents:
            scheme.documents.append(d)


def _replace_documents(db: Session, scheme: Scheme, keys: list[str]):
    docs = db.query(Document).filter(Document.key.in_(keys)).all()
    scheme.documents = []
    for d in docs:
        scheme.documents.append(d)


class PartnerRepository:
    @staticmethod
    def list(db: Session):
        return db.query(Partner).all()

    @staticmethod
    def get(db: Session, partner_id: int):
        return db.query(Partner).filter(Partner.id == partner_id).first()

    @staticmethod
    def create(db: Session, data: PartnerCreate):
        slugs = data.scheme_slugs or []
        payload = data.model_dump(exclude={"scheme_slugs"})
        partner = Partner(**payload)
        db.add(partner)
        db.flush()
        _attach_schemes(db, partner, slugs)
        db.commit()
        db.refresh(partner)
        return partner

    @staticmethod
    def update(db: Session, partner: Partner, data: dict):
        for k, v in data.items():
            if k == "scheme_slugs":
                continue
            if hasattr(partner, k) and v is not None:
                setattr(partner, k, v)
        if "scheme_slugs" in data:
            _replace_schemes(db, partner, data["scheme_slugs"] or [])
        db.commit()
        db.refresh(partner)
        return partner

    @staticmethod
    def delete(db: Session, partner: Partner):
        db.delete(partner)
        db.commit()


def _attach_schemes(db: Session, partner: Partner, slugs: list[str]):
    schemes = db.query(Scheme).filter(Scheme.slug.in_(slugs)).all()
    for s in schemes:
        if s not in partner.schemes:
            partner.schemes.append(s)


def _replace_schemes(db: Session, partner: Partner, slugs: list[str]):
    schemes = db.query(Scheme).filter(Scheme.slug.in_(slugs)).all()
    partner.schemes = []
    for s in schemes:
        partner.schemes.append(s)
