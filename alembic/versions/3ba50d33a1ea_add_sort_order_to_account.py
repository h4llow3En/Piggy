"""add_sort_order_to_account

Revision ID: 3ba50d33a1ea
Revises: 63d02dfd606f
Create Date: 2026-02-02 14:41:29.492240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ba50d33a1ea'
down_revision: Union[str, Sequence[str], None] = '63d02dfd606f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('accounts', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('accounts', 'sort_order')
