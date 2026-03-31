import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.database import get_db
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.models.company import Company
from app.services.companies import create_company, list_companies, update_company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company_endpoint(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    body: CompanyCreate,
) -> CompanyRead:
    row = create_company(db, body)
    return CompanyRead.model_validate(row)


@router.get("", response_model=list[CompanyRead])
def list_companies_endpoint(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[CompanyRead]:
    rows = list_companies(db, skip=skip, limit=limit)
    return [CompanyRead.model_validate(r) for r in rows]


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
) -> CompanyRead:
    row = db.get(Company, company_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")
    return CompanyRead.model_validate(row)


@router.patch("/{company_id}", response_model=CompanyRead)
def patch_company(
    _: Annotated[dict, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    company_id: uuid.UUID,
    body: CompanyUpdate,
) -> CompanyRead:
    row = update_company(db, company_id, body)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")
    return CompanyRead.model_validate(row)
