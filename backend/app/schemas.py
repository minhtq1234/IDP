from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import settings

DataType = Literal["string", "number", "date", "currency", "list", "object"]

FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


class FieldDef(BaseModel):
    name: str
    data_type: DataType
    required: bool = False
    hint: str = ""
    regex: str | None = None
    # Used when data_type is "list" (item shape) or "object" (properties).
    children: list["FieldDef"] | None = None

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        if not FIELD_NAME_RE.match(v):
            raise ValueError(
                "field name must be snake_case: lowercase letters, digits, "
                "underscores; start with a letter; max 63 chars"
            )
        return v

    @field_validator("hint")
    @classmethod
    def _hint_len(cls, v: str) -> str:
        if len(v) > settings.hint_max_chars:
            raise ValueError(f"hint exceeds {settings.hint_max_chars} characters")
        return v

    @model_validator(mode="after")
    def _children_consistency(self) -> "FieldDef":
        nested = self.data_type in ("list", "object")
        if nested and not self.children:
            # allow empty list while drafting, but not None
            self.children = self.children or []
        if not nested and self.children:
            raise ValueError(
                f"field '{self.name}' of type {self.data_type} cannot have children"
            )
        return self


FieldDef.model_rebuild()


class TemplateSampleRead(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Document templates ---------------------------------------------------


class DocumentTemplateBase(BaseModel):
    code: str
    name: str
    description: str = ""
    file_formats: list[str] = Field(default_factory=lambda: ["pdf", "jpg", "png"])
    active: bool = True


class DocumentTemplateCreate(DocumentTemplateBase):
    fields: list[FieldDef] = Field(default_factory=list)


class DocumentTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    file_formats: list[str] | None = None
    active: bool | None = None
    fields: list[FieldDef] | None = None


class DocumentTemplateRead(DocumentTemplateBase):
    id: UUID
    fields: list[FieldDef]

    class Config:
        from_attributes = True


# --- Application types ----------------------------------------------------


class RequiredDocument(BaseModel):
    template_id: UUID
    required: bool = True
    min_count: int = 1
    max_count: int = 1


class ApplicationTypeBase(BaseModel):
    code: str
    name: str
    description: str = ""
    active: bool = True


class ApplicationTypeCreate(ApplicationTypeBase):
    required_documents: list[RequiredDocument] = Field(default_factory=list)


class ApplicationTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None
    required_documents: list[RequiredDocument] | None = None


class ApplicationTypeRead(ApplicationTypeBase):
    id: UUID
    required_documents: list[RequiredDocument]

    class Config:
        from_attributes = True


# --- Generation -----------------------------------------------------------


class GeneratedArtifacts(BaseModel):
    json_schema: dict
    vlm_prompt: str


class FieldSuggestionRequest(BaseModel):
    document_type_name: str
    description: str = ""
    # Optional: free-text description of a sample document for the LLM.
    sample_text: str = ""


class FieldSuggestionResponse(BaseModel):
    fields: list[FieldDef]
    provider: str
