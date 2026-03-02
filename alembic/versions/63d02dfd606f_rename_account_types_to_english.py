"""rename_account_types_to_english

Revision ID: 63d02dfd606f
Revises: 23bff8742831
Create Date: 2026-02-02 14:35:35.164386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63d02dfd606f'
down_revision: Union[str, Sequence[str], None] = '23bff8742831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE accounts SET type = 'Credit Card' WHERE type = 'Kreditkarte'")
    op.execute("UPDATE accounts SET type = 'Savings' WHERE type = 'Tagesgeld'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE accounts SET type = 'Kreditkarte' WHERE type = 'Credit Card'")
    op.execute("UPDATE accounts SET type = 'Tagesgeld' WHERE type = 'Savings'")
