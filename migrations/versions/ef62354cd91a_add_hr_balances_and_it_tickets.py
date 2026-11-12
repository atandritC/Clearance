from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ef62354cd91a"
down_revision: Union[str, Sequence[str], None] = "dc5624c34f9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_leave_balances",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("annual_days_remaining", sa.Numeric(5, 1), nullable=False),
        sa.Column("sick_days_remaining", sa.Numeric(5, 1), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "it_tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_number"),
    )
    op.create_index(
        "ix_it_tickets_user_created_at",
        "it_tickets",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_it_tickets_user_created_at", table_name="it_tickets")
    op.drop_table("it_tickets")
    op.drop_table("employee_leave_balances")
