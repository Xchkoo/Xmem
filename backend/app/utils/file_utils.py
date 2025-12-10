"""
文件上传工具函数
"""
import uuid
from pathlib import Path
from fastapi import UploadFile
from typing import Union, Optional


async def save_uploaded_img(
    file: Union[UploadFile, any],
    save_dir: Path,
    default_ext: str = ".jpg"
) -> str:
    """
    保存上传的图片到指定目录
    
    Args:
        file: 上传的图片文件对象（UploadFile 或类似对象）
        save_dir: 保存目录的 Path 对象
        default_ext: 默认文件扩展名（如果无法从文件名获取）
    
    Returns:
        保存后的文件路径（字符串）
    
    Raises:
        OSError: 如果目录创建失败或文件写入失败
    """
    # 确保目录存在
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取文件扩展名
    filename = getattr(file, "filename", None)
    file_ext = Path(filename).suffix if filename else default_ext
    
    # 生成唯一文件名
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = save_dir / file_name
    
    # 读取文件内容
    if hasattr(file, "read"):
        # UploadFile 对象
        content = await file.read()
    elif hasattr(file, "file"):
        # 表单中的文件对象
        content = await file.file.read()
    else:
        raise ValueError("不支持的文件对象类型")
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(content)
    
    return str(file_path)


async def save_uploaded_file(
    file: UploadFile,
    save_dir: Path,
    max_size: Optional[int] = None,
    default_ext: str = ""
) -> tuple[str, bytes]:
    """
    保存上传的文件到指定目录（支持文件大小验证）
    
    Args:
        file: 上传的文件对象（UploadFile）
        save_dir: 保存目录的 Path 对象
        max_size: 最大文件大小（字节），如果提供则进行验证
        default_ext: 默认文件扩展名（如果无法从文件名获取）
    
    Returns:
        tuple: (保存后的文件路径, 文件内容字节)
    
    Raises:
        HTTPException: 如果文件大小超过限制
        OSError: 如果目录创建失败或文件写入失败
    """
    # 确保目录存在
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取文件内容
    content = await file.read()
    
    # 验证文件大小
    if max_size is not None and len(content) > max_size:
        from fastapi import HTTPException
        size_mb = len(content) / 1024 / 1024
        max_size_mb = max_size / 1024 / 1024
        raise HTTPException(
            status_code=400,
            detail=f"文件大小不能超过 {max_size_mb:.0f}MB，当前文件: {size_mb:.2f}MB"
        )
    
    # 获取文件扩展名
    filename = file.filename or "file"
    file_ext = Path(filename).suffix if filename else default_ext
    if not file_ext:
        file_ext = default_ext
    
    # 生成唯一文件名
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = save_dir / file_name
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(content)
    
    return str(file_path), content

