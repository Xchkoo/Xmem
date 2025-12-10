"""
Pytest 配置文件
"""
import pytest
from pathlib import Path
import os
import sys

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


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """为测试设置环境变量"""
    # 设置测试环境变量，避免影响实际配置
    monkeypatch.setenv("OCR_PROVIDER", "local")
    # 如果 TESSERACT_CMD 未设置，尝试使用系统默认路径
    if not os.getenv("TESSERACT_CMD"):
        # 不设置，让代码使用系统默认路径
        pass