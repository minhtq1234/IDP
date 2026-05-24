from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class ApplicationType(Base):
    __tablename__ = "application_types"

    id: Mapped[UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    required_documents: Mapped[list["ApplicationTypeDocument"]] = relationship(
        back_populates="application_type", cascade="all, delete-orphan"
    )


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id: Mapped[UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    # Accepted file formats, e.g. ["pdf","jpg","png"]
    file_formats: Mapped[list[str]] = mapped_column(JSONB, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    fields: Mapped[list["TemplateField"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateField.order_index",
    )


class TemplateField(Base):
    __tablename__ = "template_fields"
    __table_args__ = (UniqueConstraint("template_id", "name", name="uq_template_field_name"),)

    id: Mapped[UUID] = _uuid_pk()
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("document_templates.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(128))
    # string | number | date | currency | list | object
    data_type: Mapped[str] = mapped_column(String(32))
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    hint: Mapped[str] = mapped_column(Text, default="")
    regex: Mapped[str | None] = mapped_column(Text, nullable=True)
    # For list/object: nested field definitions (recursive JSON tree)
    children: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    template: Mapped[DocumentTemplate] = relationship(back_populates="fields")


class ApplicationTypeDocument(Base):
    __tablename__ = "application_type_documents"
    __table_args__ = (
        UniqueConstraint("application_type_id", "template_id", name="uq_app_type_template"),
    )

    id: Mapped[UUID] = _uuid_pk()
    application_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("application_types.id", ondelete="CASCADE"), index=True
    )
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("document_templates.id", ondelete="RESTRICT"), index=True
    )
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    min_count: Mapped[int] = mapped_column(Integer, default=1)
    max_count: Mapped[int] = mapped_column(Integer, default=1)

    application_type: Mapped[ApplicationType] = relationship(back_populates="required_documents")
    template: Mapped[DocumentTemplate] = relationship()
