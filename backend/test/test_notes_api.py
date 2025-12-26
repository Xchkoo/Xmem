"""
Notes API 路由测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import io
from pathlib import Path

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


@pytest.fixture
def mock_note():
    """模拟 Note 对象"""
    note = models.Note(
        id=1,
        user_id=1,
        body_md="测试笔记内容",
        images=None,
        files=None,
        attachment_url=None,
        is_pinned=False,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return note


@pytest.fixture
def sample_file_bytes():
    """创建测试文件字节流"""
    return io.BytesIO(b"test file content")


# ========== 测试创建笔记 ==========

class TestCreateNote:
    """测试创建笔记端点"""
    
    def test_create_note_success(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试成功创建笔记"""
        async def override_get_current_user():
            return mock_user
        
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
            response = client.post(
                "/notes",
                json={
                    "body_md": "# 测试笔记"
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["body_md"] == "# 测试笔记"
            assert "id" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_create_note_without_auth(self, client):
        """测试未认证创建笔记"""
        response = client.post(
            "/notes",
            json={"body_md": "测试"}
        )
        assert response.status_code == 401


# ========== 测试获取笔记列表 ==========

class TestListNotes:
    """测试获取笔记列表端点"""
    
    def test_list_notes_empty(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试获取空笔记列表"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/notes",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()
    
    def test_list_notes_with_data(
        self,
        client,
        mock_user,
        mock_token,
        mock_note
    ):
        """测试获取包含数据的笔记列表"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_note]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/notes",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_list_notes_with_search(
        self,
        client,
        mock_user,
        mock_token,
        mock_note
    ):
        """测试带搜索关键词的笔记列表"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_note]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/notes?q=测试",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_list_notes_without_auth(self, client):
        """测试未认证获取笔记列表"""
        response = client.get("/notes")
        assert response.status_code == 401


# ========== 测试上传图片 ==========

class TestUploadImage:
    """测试上传图片端点"""
    
    @patch('app.routers.notes.save_uploaded_img')
    def test_upload_image_success(
        self,
        mock_save_img,
        client,
        mock_user,
        mock_token,
        sample_image_bytes
    ):
        """测试成功上传图片"""
        mock_save_img.return_value = "uploads/images/test.jpg"
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.post(
                "/notes/upload-image",
                files={"file": ("test.png", sample_image_bytes, "image/png")},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert "test.jpg" in data["url"]
        finally:
            app.dependency_overrides.clear()
    
    def test_upload_image_without_auth(self, client, sample_image_bytes):
        """测试未认证上传图片"""
        response = client.post(
            "/notes/upload-image",
            files={"file": ("test.png", sample_image_bytes, "image/png")}
        )
        assert response.status_code == 401


# ========== 测试上传文件 ==========

class TestUploadFile:
    """测试上传文件端点"""
    
    @patch('app.routers.notes.save_uploaded_file')
    def test_upload_file_success(
        self,
        mock_save_file,
        client,
        mock_user,
        mock_token,
        sample_file_bytes
    ):
        """测试成功上传文件"""
        mock_save_file.return_value = ("uploads/files/test.txt", b"test content")
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.post(
                "/notes/upload-file",
                files={"file": ("test.txt", sample_file_bytes, "text/plain")},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert "name" in data
            assert "size" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_upload_file_without_auth(self, client, sample_file_bytes):
        """测试未认证上传文件"""
        response = client.post(
            "/notes/upload-file",
            files={"file": ("test.txt", sample_file_bytes, "text/plain")}
        )
        assert response.status_code == 401


# ========== 测试更新笔记 ==========

class TestUpdateNote:
    """测试更新笔记端点"""
    
    def test_update_note_success(
        self,
        client,
        mock_user,
        mock_token,
        mock_note
    ):
        """测试成功更新笔记"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_note
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/notes/1",
                json={
                    "body_md": "更新后的内容",
                    "images": None,
                    "files": None
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_update_note_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试更新不存在的笔记"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/notes/999",
                json={"body_md": "更新内容"},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_update_note_without_auth(self, client):
        """测试未认证更新笔记"""
        response = client.patch(
            "/notes/1",
            json={"body_md": "更新内容"}
        )
        assert response.status_code == 401


# ========== 测试删除笔记 ==========

class TestDeleteNote:
    """测试删除笔记端点"""
    
    def test_delete_note_success(
        self,
        client,
        mock_user,
        mock_token,
        mock_note
    ):
        """测试成功删除笔记"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_note
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.delete(
                "/notes/1",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
        finally:
            app.dependency_overrides.clear()
    
    def test_delete_note_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试删除不存在的笔记"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.delete(
                "/notes/999",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_delete_note_without_auth(self, client):
        """测试未认证删除笔记"""
        response = client.delete("/notes/1")
        assert response.status_code == 401


# ========== 测试置顶笔记 ==========

class TestPinNote:
    """测试置顶笔记端点"""
    
    def test_pin_note_success(
        self,
        client,
        mock_user,
        mock_token,
        mock_note
    ):
        """测试成功置顶笔记"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_note
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.is_pinned = True
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/notes/1/pin",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_pin_note_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试置顶不存在的笔记"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/notes/999/pin",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_pin_note_without_auth(self, client):
        """测试未认证置顶笔记"""
        response = client.patch("/notes/1/pin")
        assert response.status_code == 401

