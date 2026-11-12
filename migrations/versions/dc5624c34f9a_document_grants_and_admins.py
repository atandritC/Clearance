from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "dc5624c34f9a"
down_revision: Union[str, Sequence[str], None] = "cc144f1a7b2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "is_admin", server_default=None)
    op.create_table(
        "knowledge_document_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("knowledge_document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("granted_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "knowledge_document_id",
            "user_id",
            name="uq_knowledge_document_grant_user",
        ),
    )
    op.create_index(
        "ix_knowledge_document_grants_user_id",
        "knowledge_document_grants",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_document_grants")
    op.drop_column("users", "is_admin")
