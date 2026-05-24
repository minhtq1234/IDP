import pytest
from pydantic import ValidationError

from app.schemas import FieldDef


def test_field_name_rejects_camel_case():
    with pytest.raises(ValidationError):
        FieldDef(name="grossSalary", data_type="currency")


def test_field_name_rejects_leading_digit():
    with pytest.raises(ValidationError):
        FieldDef(name="1st_amount", data_type="number")


def test_field_name_accepts_snake_case():
    f = FieldDef(name="gross_salary", data_type="currency", required=True)
    assert f.name == "gross_salary"


def test_hint_length_enforced():
    with pytest.raises(ValidationError):
        FieldDef(name="x", data_type="string", hint="a" * 5000)


def test_children_only_allowed_for_nested_types():
    with pytest.raises(ValidationError):
        FieldDef(
            name="x", data_type="string",
            children=[FieldDef(name="y", data_type="string")],
        )


def test_list_field_can_have_object_children():
    f = FieldDef(
        name="transactions",
        data_type="list",
        children=[
            FieldDef(
                name="row",
                data_type="object",
                children=[
                    FieldDef(name="date", data_type="date", required=True),
                    FieldDef(name="amount", data_type="currency", required=True),
                ],
            )
        ],
    )
    assert f.children and f.children[0].children
