from app.generation import generate_json_schema, generate_vlm_prompt
from app.schemas import FieldDef


def _fields() -> list[FieldDef]:
    return [
        FieldDef(name="full_name", data_type="string", required=True, hint="Tên đầy đủ"),
        FieldDef(
            name="id_number",
            data_type="string",
            required=True,
            regex=r"^\d{12}$",
            hint="12-digit CCCD number",
        ),
        FieldDef(name="date_of_birth", data_type="date", required=True),
        FieldDef(name="gross_salary", data_type="currency", required=True),
        FieldDef(
            name="transactions",
            data_type="list",
            children=[
                FieldDef(
                    name="row",
                    data_type="object",
                    children=[
                        FieldDef(name="date", data_type="date", required=True),
                        FieldDef(name="amount", data_type="currency", required=True),
                        FieldDef(name="description", data_type="string"),
                    ],
                )
            ],
        ),
    ]


def test_json_schema_envelope():
    s = generate_json_schema("cccd", "CCCD", "Vietnamese national ID", _fields())
    assert s["type"] == "object"
    assert s["required"] == [
        "document_id",
        "document_type",
        "classification_confidence",
        "fields",
    ]
    fields_node = s["properties"]["fields"]
    assert fields_node["properties"]["id_number"]["pattern"] == r"^\d{12}$"
    assert fields_node["properties"]["date_of_birth"]["format"] == "date"
    assert fields_node["properties"]["transactions"]["type"] == "array"


def test_vlm_prompt_includes_fields_and_hints():
    fields = _fields()
    schema = generate_json_schema("cccd", "CCCD", "", fields)
    prompt = generate_vlm_prompt("cccd", "CCCD", "", fields, schema)
    assert "full_name" in prompt
    assert "Tên đầy đủ" in prompt
    assert "ISO-8601" in prompt
    assert "JSON" in prompt
