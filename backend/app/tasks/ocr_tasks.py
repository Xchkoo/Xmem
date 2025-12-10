from pathlib import Path
import logging
from ..celery_app import celery_app
from ..services.ocr import extract_text_from_image

logger = logging.getLogger(__name__)


@celery_app.task(name="ocr.extract_text")
def extract_text_from_image_task(image_path: str) -> str:
    """
    Celery 任务：从图片中提取文本（OCR）
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        提取的文本内容
    """
    try:
        logger.info(f"开始 OCR 任务，图片路径: {image_path}")
        
        # 检查文件是否存在
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 调用 OCR 服务
        text = extract_text_from_image(image_path)
        
        logger.info(f"OCR 任务完成，提取文本长度: {len(text)}")
        return text
    except Exception as e:
        logger.error(f"OCR 任务失败: {str(e)}")
        raise

