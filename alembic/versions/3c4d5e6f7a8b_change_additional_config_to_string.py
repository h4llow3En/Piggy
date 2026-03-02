"""Change additional_config to string

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-01-30 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4d5e6f7a8b'
down_revision: Union[str, Sequence[str], None] = '2b3c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change column type from JSON to String
    # Note: postgres handles casting from json to text if needed
    op.alter_column('users', 'additional_config',
               existing_type=sa.JSON(),
               type_=sa.String(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'additional_config',
               existing_type=sa.String(),
               type_=sa.JSON(),
               existing_nullable=True,
               postgresql_using='additional_config::json')
