import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.routers.notes import link_files_to_note
from app.tasks.file_tasks import _cleanup_logic
from app import models

@pytest.mark.asyncio
async def test_link_files_to_note():
    # Setup
    session = AsyncMock()
    mock_file1 = MagicMock(spec=models.File)
    mock_file1.note_id = 1
    
    mock_new_file = MagicMock(spec=models.File)
    mock_new_file.note_id = None
    
    # 配置 session.execute 的返回值
    # 第一次调用返回已关联的文件
    # 第二次调用返回新匹配的文件
    result1 = MagicMock()
    result1.scalars.return_value.all.return_value = [mock_file1]
    
    result2 = MagicMock()
    result2.scalars.return_value.all.return_value = [mock_new_file]
    
    session.execute.side_effect = [result1, result2]
    
    # Run
    body_md = "Check this out: ![](http://host/notes/files/images/img1.jpg)"
    await link_files_to_note(session, 1, body_md, user_id=123)
    
    # Verify
    # 1. 之前的文件应该被解除关联
    assert mock_file1.note_id is None
    
    # 2. 新文件应该被关联
    assert mock_new_file.note_id == 1
    
    # 3. 验证 execute 调用次数
    assert session.execute.call_count == 2

@pytest.mark.asyncio
async def test_cleanup_orphan_files():
    # Mock AsyncSessionLocal
    mock_session = AsyncMock()
    
    # Mock finding orphan files
    mock_file = MagicMock(spec=models.File)
    mock_file.file_path = "dummy_path.txt"
    
    result = MagicMock()
    result.scalars.return_value.all.return_value = [mock_file]
    mock_session.execute.return_value = result
    
    # Patch AsyncSessionLocal to return our mock session
    # Patch os functions
    with patch("app.tasks.file_tasks.AsyncSessionLocal", return_value=mock_session), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        
        # 因为 AsyncSessionLocal 是作为一个 async context manager 使用的
        # async with AsyncSessionLocal() as session:
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        await _cleanup_logic()
        
        # Verify file removed
        mock_remove.assert_called_with("dummy_path.txt")
        
        # Verify db delete
        mock_session.delete.assert_called_with(mock_file)
        mock_session.commit.assert_called_once()
