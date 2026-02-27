"""create indexes

Revision ID: 3258a671934e
Revises: 3ba50d33a1ea
Create Date: 2026-02-09 10:57:20.190096

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3258a671934e"
down_revision: Union[str, Sequence[str], None] = "3ba50d33a1ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.create_index(
            "idx_transaction_account_timestamp",
            ["account_id", "timestamp"],
            unique=False,
        )
        batch_op.create_index(
            "idx_transaction_target_account_timestamp",
            ["target_account_id", "timestamp"],
            unique=False,
        )
        batch_op.create_index("idx_transaction_type", ["type"], unique=False)

    with op.batch_alter_table("accounts") as batch_op:
        batch_op.create_index("idx_account_user_id", ["user_id"], unique=False)

    with op.batch_alter_table("users") as batch_op:
        batch_op.create_index("idx_user_id_column", ["id"], unique=False)

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.create_index(
            "idx_transaction_account_date_type",
            [
                "account_id",
                sa.text("CAST(timestamp AT TIME ZONE 'UTC' AS DATE)"),
                "type",
            ],
            unique=False,
        )

    with op.batch_alter_table("recurring_payments") as batch_op:
        batch_op.create_index(
            "idx_recurring_payment_user_type_name_amount",
            ["user_id", "type", "name", "amount"],
            unique=False,
        )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.create_index(
            "idx_transaction_timestamp_parts",
            [
                sa.text("EXTRACT(MONTH FROM timestamp AT TIME ZONE 'UTC')"),
                sa.text("EXTRACT(YEAR FROM timestamp AT TIME ZONE 'UTC')"),
            ],
            unique=False,
        )

    with op.batch_alter_table("budgets") as batch_op:
        batch_op.create_index(
            "idx_budget_user_category", ["user_id", "category_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("budgets") as batch_op:
        batch_op.drop_index("idx_budget_user_category")

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_index("idx_transaction_timestamp_parts")

    with op.batch_alter_table("recurring_payments") as batch_op:
        batch_op.drop_index("idx_recurring_payment_user_type_name_amount")

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_index("idx_transaction_account_date_type")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("idx_user_id_column")

    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_index("idx_account_user_id")

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_index("idx_transaction_type")
        batch_op.drop_index("idx_transaction_target_account_timestamp")
        batch_op.drop_index("idx_transaction_account_timestamp")
