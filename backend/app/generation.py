"""Schema + VLM prompt generation from a template definition.

Centralised so US-E0-06 AC#4 holds: changes to the prompting strategy
apply across all templates without per-template rework.
"""
from __future__ import annotations

from app.schemas import FieldDef

JSON_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "date": "string",  # ISO-8601, enforced via format
    "currency": "number",
}


def _field_to_schema(field: FieldDef) -> dict:
    if field.data_type == "object":
        props = {f.name: _field_to_schema(f) for f in field.children or []}
        required = [f.name for f in field.children or [] if f.required]
        node: dict = {"type": "object", "properties": props}
        if required:
            node["required"] = required
    elif field.data_type == "list":
        item_shape: dict
        if field.children and len(field.children) == 1 and field.children[0].data_type in (
            "string",
            "number",
            "date",
            "currency",
        ):
            item_shape = _field_to_schema(field.children[0])
        elif field.children:
            props = {f.name: _field_to_schema(f) for f in field.children}
            required = [f.name for f in field.children if f.required]
            item_shape = {"type": "object", "properties": props}
            if required:
                item_shape["required"] = required
        else:
            item_shape = {"type": "string"}
        node = {"type": "array", "items": item_shape}
    else:
        node = {"type": JSON_TYPE_MAP[field.data_type]}
        if field.data_type == "date":
            node["format"] = "date"
        if field.data_type == "currency":
            node["x-format"] = "currency"

    if field.regex:
        node["pattern"] = field.regex
    if field.hint:
        node["description"] = field.hint
    return node


def generate_json_schema(
    template_code: str,
    template_name: str,
    description: str,
    fields: list[FieldDef],
) -> dict:
    """Generate the standard extraction envelope.

    Envelope: document_id, document_type, classification_confidence, fields[].
    The `fields` member is constrained by the template's field definitions.
    """
    properties = {f.name: _field_to_schema(f) for f in fields}
    required = [f.name for f in fields if f.required]
    field_object: dict = {"type": "object", "properties": properties}
    if required:
        field_object["required"] = required

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"idp://templates/{template_code}",
        "title": template_name,
        "description": description or f"Extraction output for {template_name}",
        "type": "object",
        "required": ["document_id", "document_type", "classification_confidence", "fields"],
        "properties": {
            "document_id": {"type": "string"},
            "document_type": {"const": template_code},
            "classification_confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "fields": field_object,
        },
    }


def _format_field_for_prompt(field: FieldDef, depth: int = 0) -> str:
    indent = "  " * depth
    parts = [f"{indent}- `{field.name}` ({field.data_type})"]
    if field.required:
        parts.append("[required]")
    if field.regex:
        parts.append(f"[pattern: {field.regex}]")
    line = " ".join(parts)
    if field.hint:
        line += f"\n{indent}  hint: {field.hint}"
    if field.children:
        line += "\n" + "\n".join(_format_field_for_prompt(c, depth + 1) for c in field.children)
    return line


PROMPT_TEMPLATE = """You are a document extraction VLM. Extract structured \
data from the attached document.

DOCUMENT TYPE: {template_name} ({template_code})
{description_block}
FIELDS TO EXTRACT:
{field_block}

INSTRUCTIONS:
1. Read the document carefully and locate each field above.
2. If a required field is not visible, return null and lower your confidence.
3. For dates, normalise to ISO-8601 (YYYY-MM-DD).
4. For currency, return a JSON number in the document's native units; do not \
add separators or symbols.
5. Respect any regex patterns provided.
6. Return ONLY a single JSON object that conforms exactly to this schema:

{schema_excerpt}

Do not include explanations, markdown fences, or any text outside the JSON object.
"""


def generate_vlm_prompt(
    template_code: str,
    template_name: str,
    description: str,
    fields: list[FieldDef],
    json_schema: dict,
) -> str:
    field_block = "\n".join(_format_field_for_prompt(f) for f in fields) or "(no fields defined)"
    description_block = f"DESCRIPTION: {description}\n" if description else ""
    import json

    schema_excerpt = json.dumps(json_schema["properties"]["fields"], indent=2)
    return PROMPT_TEMPLATE.format(
        template_name=template_name,
        template_code=template_code,
        description_block=description_block,
        field_block=field_block,
        schema_excerpt=schema_excerpt,
    )
