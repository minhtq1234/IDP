from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.db import get_db
from app.schemas import TemplateSampleRead

router = APIRouter(prefix="/document-templates/{template_id}/samples", tags=["samples"])

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
}


def _storage_root() -> Path:
    p = Path(settings.sample_storage_dir).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.get("", response_model=list[TemplateSampleRead])
def list_samples(template_id: UUID, db: Session = Depends(get_db)):
    if not db.get(models.DocumentTemplate, template_id):
        raise HTTPException(404, "template not found")
    rows = db.scalars(
        select(models.TemplateSample)
        .where(models.TemplateSample.template_id == template_id)
        .order_by(models.TemplateSample.uploaded_at.desc())
    ).all()
    return rows


@router.post("", response_model=TemplateSampleRead, status_code=201)
async def upload_sample(
    template_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not db.get(models.DocumentTemplate, template_id):
        raise HTTPException(404, "template not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f"unsupported content-type: {file.content_type}")

    contents = await file.read()
    if len(contents) > settings.max_sample_bytes:
        raise HTTPException(413, f"file exceeds {settings.max_sample_bytes} bytes")

    folder = _storage_root() / str(template_id)
    folder.mkdir(parents=True, exist_ok=True)
    sample_id = uuid4()
    ext = ALLOWED_TYPES[file.content_type]
    path = folder / f"{sample_id}.{ext}"
    path.write_bytes(contents)

    row = models.TemplateSample(
        id=sample_id,
        template_id=template_id,
        filename=file.filename or f"sample.{ext}",
        content_type=file.content_type,
        size_bytes=len(contents),
        storage_path=str(path),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{sample_id}/download")
def download_sample(template_id: UUID, sample_id: UUID, db: Session = Depends(get_db)):
    row = db.get(models.TemplateSample, sample_id)
    if not row or row.template_id != template_id:
        raise HTTPException(404)
    return FileResponse(row.storage_path, media_type=row.content_type, filename=row.filename)


@router.delete("/{sample_id}", status_code=204)
def delete_sample(template_id: UUID, sample_id: UUID, db: Session = Depends(get_db)):
    row = db.get(models.TemplateSample, sample_id)
    if not row or row.template_id != template_id:
        raise HTTPException(404)
    try:
        Path(row.storage_path).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(row)
    db.commit()
