"""remove_body_field_and_make_body_md_required

Revision ID: 9f82752ac1ea
Revises: f9f7d042d713
Create Date: 2025-12-10 03:12:16.210726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f82752ac1ea'
down_revision: Union[str, None] = 'f9f7d042d713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 先迁移数据：将 body 的内容复制到 body_md（如果 body_md 为空且 body 不为空）
    op.execute("""
        UPDATE notes 
        SET body_md = body 
        WHERE (body_md IS NULL OR body_md = '') 
        AND body IS NOT NULL 
        AND body != ''
    """)
    
    # 2. 将 body_md 设为非空（必填）
    op.alter_column('notes', 'body_md',
                    existing_type=sa.Text(),
                    nullable=False,
                    server_default='')
    
    # 3. 删除 body 字段
    op.drop_column('notes', 'body')


def downgrade() -> None:
    # 1. 重新添加 body 字段
    op.add_column('notes', sa.Column('body', sa.Text(), nullable=False, server_default=''))
    
    # 2. 将 body_md 的内容复制回 body（取前100字符用于兼容）
    op.execute("""
        UPDATE notes 
        SET body = CASE 
            WHEN LENGTH(body_md) > 100 THEN SUBSTRING(body_md, 1, 100)
            ELSE body_md
        END
        WHERE body_md IS NOT NULL
    """)
    
    # 3. 将 body_md 改回可空
    op.alter_column('notes', 'body_md',
                    existing_type=sa.Text(),
                    nullable=True)
