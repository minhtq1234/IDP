from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

DataType = Literal["string", "number", "date", "currency", "list", "object"]


class FieldDef(BaseModel):
    name: str
    data_type: DataType
    required: bool = False
    hint: str = ""
    regex: str | None = None
    # Used when data_type is "list" (item shape) or "object" (properties).
    children: list[FieldDef] | None = None


FieldDef.model_rebuild()


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
