"""
Drop tan_medium and auto_sync_enabled from bank_connections

Revision ID: b2a1c3d4e5f6
Revises: ef275388e462
Create Date: 2026-02-24 14:20:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2a1c3d4e5f6"
down_revision = "8a1b2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bank_connections") as batch_op:
        # Drop columns if they exist
        try:
            batch_op.drop_column("tan_medium")
        except Exception:
            pass
        try:
            batch_op.drop_column("auto_sync_enabled")
        except Exception:
            pass


def downgrade() -> None:
    with op.batch_alter_table("bank_connections") as batch_op:
        batch_op.add_column(
            sa.Column("tan_medium", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "auto_sync_enabled",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("false"),
            )
        )
