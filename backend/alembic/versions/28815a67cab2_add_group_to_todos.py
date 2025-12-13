"""add_group_to_todos

Revision ID: 28815a67cab2
Revises: 9ca5c4231ab8
Create Date: 2025-12-13 22:27:53.329971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28815a67cab2'
down_revision: Union[str, None] = '9ca5c4231ab8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
