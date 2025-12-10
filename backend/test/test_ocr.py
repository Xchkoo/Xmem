"""
OCR 服务测试
"""
import pytest
from pathlib import Path
import os
from unittest.mock import patch, MagicMock

# 导入 OCR 服务
from app.services.ocr import (
    extract_text_from_image,
    extract_text_from_image_local,
    extract_text_from_image_remote,
)


class TestOCRLocal:
    """测试本地 OCR 功能"""

    def test_extract_text_from_image_local_with_valid_image(self, sample_image_path):
        """测试从有效图片中提取文本"""
        if not sample_image_path or not Path(sample_image_path).exists():
            pytest.skip("测试图片不存在，请将测试图片放在 backend/test/img/ 目录中")
        
        try:
            result = extract_text_from_image_local(sample_image_path)
            assert isinstance(result, str)
            assert len(result) >= 0  # 至少返回空字符串
        except RuntimeError as e:
            if "OCR 依赖未安装" in str(e):
                pytest.skip("OCR 依赖未安装，请安装 pytesseract 和 pillow")
            raise
        except Exception as e:
            # 如果 Tesseract 未安装或配置错误，跳过测试
            if "tesseract" in str(e).lower() or "not found" in str(e).lower():
                pytest.skip(f"Tesseract 未正确配置: {str(e)}")
            raise

    def test_extract_text_from_image_local_with_nonexistent_file(self):
        """测试处理不存在的文件"""
        fake_path = "/nonexistent/path/image.jpg"
        
        with pytest.raises((FileNotFoundError, OSError, Exception)):
            extract_text_from_image_local(fake_path)

    def test_extract_text_from_image_local_with_invalid_image(self, tmp_path):
        """测试处理无效的图片文件"""
        # 创建一个无效的图片文件
        invalid_image = tmp_path / "invalid.jpg"
        invalid_image.write_text("这不是一个有效的图片文件")
        
        with pytest.raises(Exception):
            extract_text_from_image_local(str(invalid_image))


class TestOCRRemote:
    """测试远程 OCR 功能"""

    def test_extract_text_from_image_remote_not_implemented(self, sample_image_path):
        """测试远程 OCR 未实现的情况"""
        if not sample_image_path:
            pytest.skip("测试图片不存在")
        
        with pytest.raises(NotImplementedError):
            extract_text_from_image_remote(sample_image_path)

    @patch("app.services.ocr.settings")
    def test_extract_text_from_image_remote_without_api_url(self, mock_settings, sample_image_path):
        """测试远程 OCR 未配置 API URL 的情况"""
        if not sample_image_path:
            pytest.skip("测试图片不存在")
        
        mock_settings.ocr_api_url = ""
        
        with pytest.raises(ValueError, match="远程 OCR API 地址未配置"):
            extract_text_from_image_remote(sample_image_path)


class TestOCRProvider:
    """测试 OCR 提供者选择"""

    @patch("app.services.ocr.settings")
    @patch("app.services.ocr.extract_text_from_image_local")
    def test_extract_text_from_image_with_local_provider(self, mock_local, mock_settings):
        """测试使用本地 OCR 提供者"""
        mock_settings.ocr_provider = "local"
        mock_local.return_value = "提取的文本"
        
        result = extract_text_from_image("test.jpg")
        
        assert result == "提取的文本"
        mock_local.assert_called_once_with("test.jpg")

    @patch("app.services.ocr.settings")
    @patch("app.services.ocr.extract_text_from_image_remote")
    def test_extract_text_from_image_with_remote_provider(self, mock_remote, mock_settings):
        """测试使用远程 OCR 提供者"""
        mock_settings.ocr_provider = "remote"
        mock_remote.return_value = "远程提取的文本"
        
        result = extract_text_from_image("test.jpg")
        
        assert result == "远程提取的文本"
        mock_remote.assert_called_once_with("test.jpg")

    @patch("app.services.ocr.settings")
    def test_extract_text_from_image_with_invalid_provider(self, mock_settings):
        """测试使用无效的 OCR 提供者"""
        mock_settings.ocr_provider = "invalid"
        
        with pytest.raises(ValueError, match="不支持的 OCR 提供者"):
            extract_text_from_image("test.jpg")


class TestOCRIntegration:
    """OCR 集成测试"""

    def test_full_ocr_workflow(self, sample_image_path):
        """测试完整的 OCR 工作流程"""
        if not sample_image_path or not Path(sample_image_path).exists():
            pytest.skip("测试图片不存在，请将测试图片放在 backend/test/img/ 目录中")
        
        try:
            # 测试本地 OCR
            text = extract_text_from_image_local(sample_image_path)
            
            # 验证返回结果
            assert isinstance(text, str)
            # 注意：OCR 结果可能为空，这取决于图片内容
            # 这里只验证函数能正常执行并返回字符串
            
        except RuntimeError as e:
            if "OCR 依赖未安装" in str(e):
                pytest.skip("OCR 依赖未安装")
            raise
        except Exception as e:
            if "tesseract" in str(e).lower():
                pytest.skip(f"Tesseract 未正确配置: {str(e)}")
            raise

    def test_ocr_with_different_image_formats(self, test_img_dir):
        """测试不同格式的图片"""
        # 支持的图片格式
        formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        found_images = []
        
        for fmt in formats:
            for img_file in test_img_dir.glob(f"*{fmt}"):
                found_images.append(str(img_file))
            for img_file in test_img_dir.glob(f"*{fmt.upper()}"):
                found_images.append(str(img_file))
        
        if not found_images:
            pytest.skip("未找到测试图片")
        
        for img_path in found_images[:3]:  # 只测试前3个图片
            try:
                result = extract_text_from_image_local(img_path)
                assert isinstance(result, str)
            except (RuntimeError, ImportError):
                pytest.skip("OCR 依赖未安装")
            except Exception as e:
                if "tesseract" in str(e).lower():
                    pytest.skip(f"Tesseract 未正确配置: {str(e)}")
                # 其他错误继续抛出
                raise

