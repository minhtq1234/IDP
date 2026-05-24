"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_application_types_code", "application_types", ["code"], unique=True)

    op.create_table(
        "document_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("file_formats", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_document_templates_code", "document_templates", ["code"], unique=True)

    op.create_table(
        "template_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("data_type", sa.String(32), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hint", sa.Text(), nullable=False, server_default=""),
        sa.Column("regex", sa.Text(), nullable=True),
        sa.Column("children", postgresql.JSONB(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("template_id", "name", name="uq_template_field_name"),
    )
    op.create_index("ix_template_fields_template_id", "template_fields", ["template_id"])

    op.create_table(
        "application_type_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("application_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_templates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_count", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint(
            "application_type_id", "template_id", name="uq_app_type_template"
        ),
    )
    op.create_index(
        "ix_app_type_documents_app_type",
        "application_type_documents",
        ["application_type_id"],
    )
    op.create_index(
        "ix_app_type_documents_template",
        "application_type_documents",
        ["template_id"],
    )


def downgrade() -> None:
    op.drop_table("application_type_documents")
    op.drop_table("template_fields")
    op.drop_table("document_templates")
    op.drop_table("application_types")
