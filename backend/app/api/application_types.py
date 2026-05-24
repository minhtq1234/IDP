from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db import get_db
from app.schemas import (
    ApplicationTypeCreate,
    ApplicationTypeRead,
    ApplicationTypeUpdate,
    RequiredDocument,
)

router = APIRouter(prefix="/application-types", tags=["application-types"])


def _to_read(at: models.ApplicationType) -> ApplicationTypeRead:
    return ApplicationTypeRead(
        id=at.id,
        code=at.code,
        name=at.name,
        description=at.description,
        active=at.active,
        required_documents=[
            RequiredDocument(
                template_id=d.template_id,
                required=d.required,
                min_count=d.min_count,
                max_count=d.max_count,
            )
            for d in at.required_documents
        ],
    )


@router.get("", response_model=list[ApplicationTypeRead])
def list_application_types(db: Session = Depends(get_db)) -> list[ApplicationTypeRead]:
    rows = db.scalars(
        select(models.ApplicationType).options(selectinload(models.ApplicationType.required_documents))
    ).all()
    return [_to_read(r) for r in rows]


@router.post("", response_model=ApplicationTypeRead, status_code=201)
def create_application_type(
    payload: ApplicationTypeCreate, db: Session = Depends(get_db)
) -> ApplicationTypeRead:
    at = models.ApplicationType(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        active=payload.active,
    )
    at.required_documents = [
        models.ApplicationTypeDocument(
            template_id=d.template_id,
            required=d.required,
            min_count=d.min_count,
            max_count=d.max_count,
        )
        for d in payload.required_documents
    ]
    db.add(at)
    db.commit()
    db.refresh(at)
    return _to_read(at)


@router.get("/{at_id}", response_model=ApplicationTypeRead)
def get_application_type(at_id: UUID, db: Session = Depends(get_db)) -> ApplicationTypeRead:
    at = db.get(models.ApplicationType, at_id)
    if not at:
        raise HTTPException(404)
    return _to_read(at)


@router.patch("/{at_id}", response_model=ApplicationTypeRead)
def update_application_type(
    at_id: UUID, payload: ApplicationTypeUpdate, db: Session = Depends(get_db)
) -> ApplicationTypeRead:
    at = db.get(models.ApplicationType, at_id)
    if not at:
        raise HTTPException(404)
    if payload.name is not None:
        at.name = payload.name
    if payload.description is not None:
        at.description = payload.description
    if payload.active is not None:
        at.active = payload.active
    if payload.required_documents is not None:
        at.required_documents.clear()
        db.flush()
        at.required_documents = [
            models.ApplicationTypeDocument(
                template_id=d.template_id,
                required=d.required,
                min_count=d.min_count,
                max_count=d.max_count,
            )
            for d in payload.required_documents
        ]
    db.commit()
    db.refresh(at)
    return _to_read(at)
