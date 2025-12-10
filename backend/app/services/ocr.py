from pathlib import Path
from typing import Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)


def extract_text_from_image_local(image_path: str) -> str:
    """
    使用本地 OCR（pytesseract）从图片中提取文本
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        提取的文本内容
    """
    try:
        import pytesseract
        from PIL import Image
        
        # 如果配置了 tesseract_cmd，则使用指定的路径
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        
        # 读取图片
        image = Image.open(image_path)
        
        # 执行 OCR
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')  # 支持中文和英文
        
        logger.info(f"本地 OCR 成功提取文本，长度: {len(text)}")
        return text.strip()
    except ImportError:
        logger.error("pytesseract 或 PIL 未安装，请安装依赖: pip install pytesseract pillow")
        raise RuntimeError("OCR 依赖未安装")
    except Exception as e:
        logger.error(f"本地 OCR 失败: {str(e)}")
        raise


def extract_text_from_image_remote(image_path: str) -> str:
    """
    使用远程 OCR API 从图片中提取文本
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        提取的文本内容
    """
    # TODO: 实现远程 OCR API 调用
    # 示例实现思路：
    # 1. 读取图片文件
    # 2. 调用远程 OCR API（如百度 OCR、腾讯 OCR、Google Vision API 等）
    # 3. 解析返回结果
    # 4. 返回提取的文本
    
    if not settings.ocr_api_url:
        raise ValueError("远程 OCR API 地址未配置（OCR_API_URL）")
    
    logger.warning("远程 OCR API 尚未实现，请配置具体的 API 地址和调用逻辑")
    raise NotImplementedError("远程 OCR API 尚未实现")


def extract_text_from_image(image_path: str) -> str:
    """
    从图片中提取文本（OCR）
    根据配置选择本地或远程 OCR
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        提取的文本内容
    """
    if settings.ocr_provider == "local":
        return extract_text_from_image_local(image_path)
    elif settings.ocr_provider == "remote":
        return extract_text_from_image_remote(image_path)
    else:
        raise ValueError(f"不支持的 OCR 提供者: {settings.ocr_provider}，请设置为 'local' 或 'remote'")

