"""
Pytest 配置文件
"""
import pytest
from pathlib import Path
import os
import sys
import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from PIL import Image

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 测试图片目录
TEST_IMG_DIR = Path(__file__).parent / "img"


@pytest.fixture
def test_img_dir():
    """返回测试图片目录路径"""
    return TEST_IMG_DIR


@pytest.fixture
def sample_image_path(test_img_dir):
    """返回示例图片路径（如果存在）"""
    # 查找目录中的第一个图片文件
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]
    for ext in image_extensions:
        for img_file in test_img_dir.glob(f"*{ext}"):
            return str(img_file)
        for img_file in test_img_dir.glob(f"*{ext.upper()}"):
            return str(img_file)
    return None


@pytest.fixture
def sample_image_bytes():
    """创建测试图片字节流"""
    # 创建一个简单的测试图片（100x100 像素的 PNG）
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def mock_user():
    """模拟用户对象"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.user_name = "Test User"
    return user


@pytest.fixture
def mock_ledger_entry():
    """模拟 LedgerEntry 对象"""
    from app import models
    entry = models.LedgerEntry(
        id=1,
        user_id=1,
        raw_text="测试文本",
        status="pending",
        amount=None,
        currency="CNY",
        category=None,
        merchant=None,
        event_time=None,
        meta=None,
        task_id=None,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=None
    )
    return entry


@pytest.fixture
def mock_async_session():
    """模拟异步数据库会话"""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.query = MagicMock()
    return session


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """为测试设置环境变量"""
    # 设置测试环境变量，避免影响实际配置
    monkeypatch.setenv("OCR_PROVIDER", "local")
    # 如果 TESSERACT_CMD 未设置，尝试使用系统默认路径
    if not os.getenv("TESSERACT_CMD"):
        # 不设置，让代码使用系统默认路径
        pass