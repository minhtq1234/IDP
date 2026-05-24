from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.db import get_db
from app.schemas import (
    DocumentTemplateCreate,
    DocumentTemplateRead,
    DocumentTemplateUpdate,
    FieldDef,
    GeneratedArtifacts,
)
from app.generation import generate_json_schema, generate_vlm_prompt

router = APIRouter(prefix="/document-templates", tags=["document-templates"])


def _field_to_def(f: models.TemplateField) -> FieldDef:
    children = None
    if f.children:
        children = [FieldDef.model_validate(c) for c in f.children]
    return FieldDef(
        name=f.name,
        data_type=f.data_type,
        required=f.required,
        hint=f.hint,
        regex=f.regex,
        children=children,
    )


def _to_read(t: models.DocumentTemplate) -> DocumentTemplateRead:
    return DocumentTemplateRead(
        id=t.id,
        code=t.code,
        name=t.name,
        description=t.description,
        file_formats=t.file_formats or [],
        active=t.active,
        fields=[_field_to_def(f) for f in t.fields],
    )


def _persist_fields(t: models.DocumentTemplate, fields: list[FieldDef]) -> None:
    t.fields.clear()
    for i, fd in enumerate(fields):
        t.fields.append(
            models.TemplateField(
                name=fd.name,
                data_type=fd.data_type,
                required=fd.required,
                hint=fd.hint,
                regex=fd.regex,
                children=[c.model_dump() for c in fd.children] if fd.children else None,
                order_index=i,
            )
        )


@router.get("", response_model=list[DocumentTemplateRead])
def list_templates(db: Session = Depends(get_db)) -> list[DocumentTemplateRead]:
    rows = db.scalars(
        select(models.DocumentTemplate).options(selectinload(models.DocumentTemplate.fields))
    ).all()
    return [_to_read(r) for r in rows]


@router.post("", response_model=DocumentTemplateRead, status_code=201)
def create_template(
    payload: DocumentTemplateCreate, db: Session = Depends(get_db)
) -> DocumentTemplateRead:
    t = models.DocumentTemplate(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        file_formats=payload.file_formats,
        active=payload.active,
    )
    _persist_fields(t, payload.fields)
    db.add(t)
    db.commit()
    db.refresh(t)
    return _to_read(t)


@router.get("/{tid}", response_model=DocumentTemplateRead)
def get_template(tid: UUID, db: Session = Depends(get_db)) -> DocumentTemplateRead:
    t = db.get(models.DocumentTemplate, tid)
    if not t:
        raise HTTPException(404)
    return _to_read(t)


@router.patch("/{tid}", response_model=DocumentTemplateRead)
def update_template(
    tid: UUID, payload: DocumentTemplateUpdate, db: Session = Depends(get_db)
) -> DocumentTemplateRead:
    t = db.get(models.DocumentTemplate, tid)
    if not t:
        raise HTTPException(404)
    if payload.name is not None:
        t.name = payload.name
    if payload.description is not None:
        t.description = payload.description
    if payload.file_formats is not None:
        t.file_formats = payload.file_formats
    if payload.active is not None:
        t.active = payload.active
    if payload.fields is not None:
        _persist_fields(t, payload.fields)
    db.commit()
    db.refresh(t)
    return _to_read(t)


@router.get("/{tid}/artifacts", response_model=GeneratedArtifacts)
def get_template_artifacts(tid: UUID, db: Session = Depends(get_db)) -> GeneratedArtifacts:
    """US-E0-05 + US-E0-06: auto-generated JSON schema and VLM prompt."""
    t = db.get(models.DocumentTemplate, tid)
    if not t:
        raise HTTPException(404)
    fields = [_field_to_def(f) for f in t.fields]
    schema = generate_json_schema(t.code, t.name, t.description, fields)
    prompt = generate_vlm_prompt(t.code, t.name, t.description, fields, schema)
    return GeneratedArtifacts(json_schema=schema, vlm_prompt=prompt)
