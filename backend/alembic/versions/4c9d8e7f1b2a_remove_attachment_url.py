"""remove attachment_url from notes

Revision ID: 4c9d8e7f1b2a
Revises: 2f840e72ac66
Create Date: 2025-12-26 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c9d8e7f1b2a'
down_revision: Union[str, None] = '2f840e72ac66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('notes', 'attachment_url')


def downgrade() -> None:
    op.add_column('notes', sa.Column('attachment_url', sa.String(length=512), nullable=True))
