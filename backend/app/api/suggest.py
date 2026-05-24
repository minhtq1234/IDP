from fastapi import APIRouter, HTTPException

from app.llm import get_llm
from app.schemas import FieldDef, FieldSuggestionRequest, FieldSuggestionResponse

router = APIRouter(prefix="/suggest", tags=["suggest"])


SYSTEM = """You assist a System Admin in defining a document extraction template.

Given a document type and an optional sample-text excerpt, propose the fields a VLM
should extract. Respond with a JSON object: {"fields": [ {name, data_type, required, hint, regex?, children?} ]}.

Allowed data_type values: "string", "number", "date", "currency", "list", "object".
Use "list" for repeating rows (e.g., transactions) and provide one item shape in `children`.
Use "object" for nested groups (e.g., address) and provide its properties in `children`.
Hints must be concise extraction guidance, not values.
"""


@router.post("", response_model=FieldSuggestionResponse)
async def suggest_fields(req: FieldSuggestionRequest) -> FieldSuggestionResponse:
    llm = get_llm()
    user = (
        f"Document type: {req.document_type_name}\n"
        f"Description: {req.description or '(none)'}\n"
        f"Sample text excerpt:\n{req.sample_text or '(none provided)'}"
    )
    try:
        data = await llm.complete_json(SYSTEM, user)
    except Exception as e:  # surface upstream provider issues to the admin
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}") from e

    raw = data.get("fields", [])
    fields = [FieldDef.model_validate(f) for f in raw]
    return FieldSuggestionResponse(fields=fields, provider=llm.name)
