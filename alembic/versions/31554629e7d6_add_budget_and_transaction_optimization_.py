"""add_budget_and_transaction_optimization_indexes

Revision ID: 31554629e7d6
Revises: 3258a671934e
Create Date: 2026-02-13 15:22:04.656014

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "31554629e7d6"
down_revision: Union[str, Sequence[str], None] = "3258a671934e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "idx_transaction_category_timestamp_type",
        "transactions",
        ["category_id", "timestamp", "type"],
        unique=False,
    )
    op.create_index("idx_budget_category_id", "budgets", ["category_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_budget_category_id", table_name="budgets")
    op.drop_index("idx_transaction_category_timestamp_type", table_name="transactions")
