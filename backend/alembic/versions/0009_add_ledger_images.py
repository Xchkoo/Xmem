"""给 ledger_entries 增加原图与缩略图字段

Revision ID: 0009_add_ledger_images
Revises: 0008_add_budget_currency
Create Date: 2026-11-08

背景：截图记账上传的图片此前只存在于请求内存与 Celery 任务中，请求结束后路径丢失，
导致"记账详情看不到原图"。这里把原图与缩略图路径落到表上长期保留，
OCR 文本只作为 AI 的输入继续留在 raw_text 里。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0009_add_ledger_images"
down_revision = "0008_add_budget_currency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ledger_entries", sa.Column("image_path", sa.String(length=512), nullable=True))
    op.add_column("ledger_entries", sa.Column("image_thumb_path", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("ledger_entries", "image_thumb_path")
    op.drop_column("ledger_entries", "image_path")
