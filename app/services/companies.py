import uuid

from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


def create_company(db: Session, data: CompanyCreate) -> Company:
    row = Company(
        legal_name=data.legal_name,
        contact_name=data.contact_name,
        email=str(data.email),
        phone=data.phone,
        status=data.status.value,
        notes=data.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_company(db: Session, company_id: uuid.UUID, data: CompanyUpdate) -> Company | None:
    row = db.get(Company, company_id)
    if not row:
        return None
    if data.legal_name is not None:
        row.legal_name = data.legal_name
    if data.contact_name is not None:
        row.contact_name = data.contact_name
    if data.email is not None:
        row.email = str(data.email)
    if data.phone is not None:
        row.phone = data.phone
    if data.status is not None:
        row.status = data.status.value
    if data.notes is not None:
        row.notes = data.notes
    db.commit()
    db.refresh(row)
    return row


def list_companies(db: Session, *, skip: int = 0, limit: int = 100) -> list[Company]:
    return db.query(Company).order_by(Company.created_at.desc()).offset(skip).limit(limit).all()
