from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cc144f1a7b2e"
down_revision: Union[str, Sequence[str], None] = "a06f8933a2eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default="!"),
    )
    op.alter_column("users", "hashed_password", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
