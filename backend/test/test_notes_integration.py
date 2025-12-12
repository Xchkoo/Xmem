"""
Notes 集成测试
测试完整的笔记操作流程
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import io

from app.main import app
from app import models
from app.db import get_session
from app.auth import get_current_user


# ========== Fixtures ==========

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_dependencies():
    """每个测试后重置依赖覆盖"""
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """模拟用户对象"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_token():
    """模拟 token"""
    return "test_token_12345"


# ========== 测试完整流程 ==========

class TestNotesIntegration:
    """测试完整的笔记操作流程"""
    
    def test_full_flow_create_list_update_delete(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试完整的笔记流程：创建 -> 列表 -> 更新 -> 删除"""
        notes_list = []
        note_id_counter = [1]  # 使用列表以便在闭包中修改
        
        # 1. 创建笔记
        async def override_get_session_create():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = note_id_counter[0]
                obj.is_pinned = False
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
                obj.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                notes_list.append(obj)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_create
        
        try:
            create_response = client.post(
                "/notes",
                json={
                    "body_md": "# 测试笔记",
                    "images": None,
                    "files": None
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert create_response.status_code == 200
            created_note = create_response.json()
            note_id = created_note["id"]
            assert created_note["body_md"] == "# 测试笔记"
        finally:
            app.dependency_overrides.clear()
        
        # 2. 获取笔记列表
        created_note_obj = models.Note(
            id=note_id,
            user_id=1,
            body_md="# 测试笔记",
            is_pinned=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        async def override_get_session_list():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [created_note_obj]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_list
        
        try:
            list_response = client.get(
                "/notes",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert list_response.status_code == 200
            notes = list_response.json()
            assert len(notes) == 1
            assert notes[0]["id"] == note_id
        finally:
            app.dependency_overrides.clear()
        
        # 3. 更新笔记
        async def override_get_session_update():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = created_note_obj
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.body_md = "更新后的内容"
                obj.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_update
        
        try:
            update_response = client.patch(
                f"/notes/{note_id}",
                json={
                    "body_md": "更新后的内容",
                    "images": None,
                    "files": None
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert update_response.status_code == 200
            updated_note = update_response.json()
            assert updated_note["id"] == note_id
        finally:
            app.dependency_overrides.clear()
        
        # 4. 删除笔记
        async def override_get_session_delete():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = created_note_obj
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_delete
        
        try:
            delete_response = client.delete(
                f"/notes/{note_id}",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert delete_response.status_code == 200
            assert delete_response.json()["ok"] is True
        finally:
            app.dependency_overrides.clear()
    
    def test_full_flow_with_pin_and_search(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试包含置顶和搜索的完整流程"""
        note1 = models.Note(
            id=1,
            user_id=1,
            body_md="置顶笔记内容",
            is_pinned=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        note2 = models.Note(
            id=2,
            user_id=1,
            body_md="普通笔记内容",
            is_pinned=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        # 1. 获取笔记列表（应该按置顶优先排序）
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            # 置顶的笔记应该在前面
            mock_result.scalars.return_value.all.return_value = [note1, note2]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            list_response = client.get(
                "/notes",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert list_response.status_code == 200
            notes = list_response.json()
            assert len(notes) == 2
            # 置顶的笔记应该在前面
            assert notes[0]["is_pinned"] is True
        finally:
            app.dependency_overrides.clear()
        
        # 2. 搜索笔记
        async def override_get_session_search():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            # 搜索应该返回匹配的笔记
            mock_result.scalars.return_value.all.return_value = [note1]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_search
        
        try:
            search_response = client.get(
                "/notes?q=置顶",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert search_response.status_code == 200
            search_results = search_response.json()
            assert len(search_results) == 1
            assert search_results[0]["id"] == 1
        finally:
            app.dependency_overrides.clear()
        
        # 3. 切换置顶状态
        async def override_get_session_pin():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = note2
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.is_pinned = True
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_pin
        
        try:
            pin_response = client.patch(
                "/notes/2/pin",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert pin_response.status_code == 200
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.routers.notes.save_uploaded_img')
    def test_full_flow_with_upload(
        self,
        mock_save_img,
        client,
        mock_user,
        mock_token,
        sample_image_bytes
    ):
        """测试包含文件上传的完整流程"""
        mock_save_img.return_value = "uploads/images/test.jpg"
        
        # 1. 上传图片
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            upload_response = client.post(
                "/notes/upload-image",
                files={"file": ("test.png", sample_image_bytes, "image/png")},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            image_url = upload_data["url"]
        finally:
            app.dependency_overrides.clear()
        
        # 2. 使用上传的图片创建笔记
        async def override_get_session():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = 1
                obj.is_pinned = False
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
                obj.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            create_response = client.post(
                "/notes",
                json={
                    "body_md": f"![图片]({image_url})",
                    "images": [image_url],
                    "files": None
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert create_response.status_code == 200
            note = create_response.json()
            assert image_url in note["images"]
        finally:
            app.dependency_overrides.clear()


# ========== 测试用户隔离 ==========

class TestNotesUserIsolation:
    """测试笔记用户隔离"""
    
    def test_users_cannot_access_others_notes(
        self,
        client,
        mock_user
    ):
        """测试用户无法访问其他用户的笔记"""
        # 用户1的笔记
        user1_note = models.Note(
            id=1,
            user_id=1,
            body_md="用户1的笔记",
            is_pinned=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        # 用户2尝试访问用户1的笔记
        user2 = MagicMock()
        user2.id = 2
        user2.email = "user2@example.com"
        
        async def override_get_current_user():
            return user2  # 当前用户是用户2
        
        async def override_get_session():
            mock_session = AsyncMock()
            # 查询时会过滤 user_id，所以返回 None
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 用户2尝试更新用户1的笔记
            response = client.patch(
                "/notes/1",
                json={"body_md": "尝试修改"},
                headers={"Authorization": "Bearer token2"}
            )
            
            # 应该返回 404，因为查询时已经过滤了 user_id
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

