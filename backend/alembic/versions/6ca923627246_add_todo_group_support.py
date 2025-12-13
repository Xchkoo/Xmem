"""add_todo_group_support

Revision ID: 6ca923627246
Revises: 28815a67cab2
Create Date: 2025-12-13 22:50:45.178341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ca923627246'
down_revision: Union[str, None] = '28815a67cab2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
