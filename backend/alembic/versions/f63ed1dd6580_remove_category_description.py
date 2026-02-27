"""remove category description

Revision ID: f63ed1dd6580
Revises: 379e2c0981ee
Create Date: 2026-02-01 19:14:32.169182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f63ed1dd6580'
down_revision: Union[str, Sequence[str], None] = '379e2c0981ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('categories', 'description')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('categories', sa.Column('description', sa.VARCHAR(length=512), autoincrement=False, nullable=True))
