"""add is_pinned to todos

Revision ID: add_is_pinned_to_todos
Revises: 6ca923627246
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_is_pinned_to_todos'
down_revision: Union[str, None] = '6ca923627246'  # 指向 add_todo_group_support 的 revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 is_pinned 字段
    op.add_column('todos', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('todos', 'is_pinned')

