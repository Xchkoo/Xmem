"""
Todos API 路由测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

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
def mock_todo():
    """模拟 Todo 对象"""
    todo = models.Todo(
        id=1,
        user_id=1,
        title="测试待办",
        completed=False,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return todo


# ========== 测试创建待办 ==========

class TestCreateTodo:
    """测试创建待办端点"""
    
    def test_create_todo_success(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试成功创建待办"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = 1
                obj.completed = False
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/todos",
                json={"title": "新待办事项"},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "新待办事项"
            assert data["completed"] is False
            assert "id" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_create_todo_without_auth(self, client):
        """测试未认证创建待办"""
        response = client.post(
            "/todos",
            json={"title": "新待办"}
        )
        assert response.status_code == 401


# ========== 测试获取待办列表 ==========

class TestListTodos:
    """测试获取待办列表端点"""
    
    def test_list_todos_empty(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试获取空待办列表"""
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
                "/todos",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()
    
    def test_list_todos_with_data(
        self,
        client,
        mock_user,
        mock_token,
        mock_todo
    ):
        """测试获取包含数据的待办列表"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_todo]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/todos",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["title"] == "测试待办"
        finally:
            app.dependency_overrides.clear()
    
    def test_list_todos_without_auth(self, client):
        """测试未认证获取待办列表"""
        response = client.get("/todos")
        assert response.status_code == 401


# ========== 测试切换待办状态 ==========

class TestToggleTodo:
    """测试切换待办状态端点"""
    
    def test_toggle_todo_to_completed(
        self,
        client,
        mock_user,
        mock_token,
        mock_todo
    ):
        """测试将待办标记为完成"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_todo
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.completed = True
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/todos/1",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_toggle_todo_to_incomplete(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试将待办标记为未完成"""
        completed_todo = models.Todo(
            id=1,
            user_id=1,
            title="已完成待办",
            completed=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = completed_todo
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.completed = False
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/todos/1",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_toggle_todo_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试切换不存在的待办状态"""
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
                "/todos/999",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_toggle_todo_without_auth(self, client):
        """测试未认证切换待办状态"""
        response = client.patch("/todos/1")
        assert response.status_code == 401


# ========== 测试删除待办 ==========

class TestDeleteTodo:
    """测试删除待办端点"""
    
    def test_delete_todo_success(
        self,
        client,
        mock_user,
        mock_token,
        mock_todo
    ):
        """测试成功删除待办"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_todo
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.delete(
                "/todos/1",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
        finally:
            app.dependency_overrides.clear()
    
    def test_delete_todo_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试删除不存在的待办"""
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
                "/todos/999",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_delete_todo_without_auth(self, client):
        """测试未认证删除待办"""
        response = client.delete("/todos/1")
        assert response.status_code == 401
    
    def test_delete_todo_user_isolation(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试用户隔离：不能删除其他用户的待办"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # 返回 None，因为查询时会过滤 user_id
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.delete(
                "/todos/2",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 应该返回 404，因为查询时已经过滤了 user_id
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

