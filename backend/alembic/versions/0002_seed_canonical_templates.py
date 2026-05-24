"""seed canonical templates (CCCD, Payslip, Bank Statement) and Retail Personal Loan

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-24
"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CCCD_FIELDS = [
    ("full_name", "string", True, "Full name as printed on the card", None, None),
    ("id_number", "string", True, "12-digit CCCD number", r"^\d{12}$", None),
    ("date_of_birth", "date", True, "Date of birth (DD/MM/YYYY on card)", None, None),
    ("sex", "string", True, "Nam / Nữ", None, None),
    ("nationality", "string", False, "Nationality, usually Việt Nam", None, None),
    ("place_of_origin", "string", False, "Quê quán", None, None),
    ("place_of_residence", "string", True, "Nơi thường trú", None, None),
]

PAYSLIP_FIELDS = [
    ("employee_name", "string", True, "Full name of the employee", None, None),
    ("employer_name", "string", True, "Name of the employing company", None, None),
    ("period", "string", True, "Pay period, e.g. 04/2026", None, None),
    ("gross_salary", "currency", True, "Gross salary; labelled Lương gộp or Tổng thu nhập", None, None),
    ("net_salary", "currency", True, "Net pay; labelled Thực lĩnh", None, None),
    ("tax_withheld", "currency", False, "Income tax withheld; labelled Thuế TNCN", None, None),
    ("social_insurance", "currency", False, "Social insurance deduction", None, None),
]

BANK_STATEMENT_FIELDS = [
    ("account_holder", "string", True, "Account holder full name", None, None),
    ("account_number", "string", True, "Bank account number", None, None),
    ("bank_name", "string", True, "Issuing bank", None, None),
    ("period_start", "date", True, "First day covered by the statement", None, None),
    ("period_end", "date", True, "Last day covered by the statement", None, None),
    ("opening_balance", "currency", True, "Balance at start of period", None, None),
    ("closing_balance", "currency", True, "Balance at end of period", None, None),
    (
        "transactions",
        "list",
        False,
        "All transaction rows in the statement table",
        None,
        [
            {"name": "date", "data_type": "date", "required": True, "hint": "Transaction date", "regex": None, "children": None},
            {"name": "description", "data_type": "string", "required": False, "hint": "Memo / counterparty", "regex": None, "children": None},
            {"name": "debit", "data_type": "currency", "required": False, "hint": "Amount out", "regex": None, "children": None},
            {"name": "credit", "data_type": "currency", "required": False, "hint": "Amount in", "regex": None, "children": None},
            {"name": "balance", "data_type": "currency", "required": False, "hint": "Running balance", "regex": None, "children": None},
        ],
    ),
]


def _insert_template(conn, code: str, name: str, description: str, fields):
    tid = uuid4()
    conn.execute(
        sa.text(
            """INSERT INTO document_templates
               (id, code, name, description, file_formats, active, created_at, updated_at)
               VALUES (:id, :code, :name, :desc, CAST(:ff AS JSONB), TRUE, NOW(), NOW())"""
        ),
        {"id": str(tid), "code": code, "name": name, "desc": description,
         "ff": json.dumps(["pdf", "jpg", "png"])},
    )
    for i, (fname, dtype, req, hint, regex, children) in enumerate(fields):
        conn.execute(
            sa.text(
                """INSERT INTO template_fields
                   (id, template_id, name, data_type, required, hint, regex, children, order_index)
                   VALUES (:id, :tid, :n, :dt, :req, :h, :rx, CAST(:ch AS JSONB), :oi)"""
            ),
            {"id": str(uuid4()), "tid": str(tid), "n": fname, "dt": dtype, "req": req,
             "h": hint, "rx": regex,
             "ch": json.dumps(children) if children else None, "oi": i},
        )
    return tid


def upgrade() -> None:
    conn = op.get_bind()
    cccd = _insert_template(conn, "cccd", "CCCD", "Vietnamese national ID card", CCCD_FIELDS)
    payslip = _insert_template(conn, "payslip", "Payslip", "Monthly salary slip", PAYSLIP_FIELDS)
    bank = _insert_template(conn, "bank_statement", "Bank Statement",
                            "Bank account statement with transaction list", BANK_STATEMENT_FIELDS)

    at_id = uuid4()
    conn.execute(
        sa.text(
            """INSERT INTO application_types
               (id, code, name, description, active, created_at, updated_at)
               VALUES (:id, :code, :name, :desc, TRUE, NOW(), NOW())"""
        ),
        {"id": str(at_id), "code": "retail_personal_loan",
         "name": "Retail Personal Loan",
         "desc": "Unsecured consumer loan for individual borrowers"},
    )
    for tid, required, mn, mx in [(cccd, True, 1, 1), (payslip, True, 1, 3), (bank, True, 3, 6)]:
        conn.execute(
            sa.text(
                """INSERT INTO application_type_documents
                   (id, application_type_id, template_id, required, min_count, max_count)
                   VALUES (:id, :at, :tid, :req, :mn, :mx)"""
            ),
            {"id": str(uuid4()), "at": str(at_id), "tid": str(tid),
             "req": required, "mn": mn, "mx": mx},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM application_types WHERE code = 'retail_personal_loan'"
    ))
    conn.execute(sa.text(
        "DELETE FROM document_templates WHERE code IN ('cccd','payslip','bank_statement')"
    ))
