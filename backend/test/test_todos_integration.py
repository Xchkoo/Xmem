"""
Todos 集成测试
测试完整的待办事项操作流程
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


# ========== 测试完整流程 ==========

class TestTodosIntegration:
    """测试完整的待办事项操作流程"""
    
    def test_full_flow_create_list_toggle_delete(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试完整的待办流程：创建 -> 列表 -> 切换状态 -> 删除"""
        todos_list = []
        todo_id_counter = [1]
        
        # 1. 创建待办
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session_create():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = todo_id_counter[0]
                obj.completed = False
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
                todos_list.append(obj)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_create
        
        try:
            create_response = client.post(
                "/todos",
                json={"title": "新待办事项"},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert create_response.status_code == 200
            created_todo = create_response.json()
            todo_id = created_todo["id"]
            assert created_todo["title"] == "新待办事项"
            assert created_todo["completed"] is False
        finally:
            app.dependency_overrides.clear()
        
        # 2. 获取待办列表
        created_todo_obj = models.Todo(
            id=todo_id,
            user_id=1,
            title="新待办事项",
            completed=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        async def override_get_session_list():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [created_todo_obj]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_list
        
        try:
            list_response = client.get(
                "/todos",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert list_response.status_code == 200
            todos = list_response.json()
            assert len(todos) == 1
            assert todos[0]["id"] == todo_id
            assert todos[0]["completed"] is False
        finally:
            app.dependency_overrides.clear()
        
        # 3. 切换待办状态（标记为完成）
        async def override_get_session_toggle():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = created_todo_obj
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.completed = True
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_toggle
        
        try:
            toggle_response = client.patch(
                f"/todos/{todo_id}",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert toggle_response.status_code == 200
            toggled_todo = toggle_response.json()
            assert toggled_todo["id"] == todo_id
        finally:
            app.dependency_overrides.clear()
        
        # 4. 再次切换（标记为未完成）
        created_todo_obj.completed = True
        
        async def override_get_session_toggle_again():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = created_todo_obj
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.completed = False
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_toggle_again
        
        try:
            toggle_again_response = client.patch(
                f"/todos/{todo_id}",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert toggle_again_response.status_code == 200
        finally:
            app.dependency_overrides.clear()
        
        # 5. 删除待办
        created_todo_obj.completed = False
        
        async def override_get_session_delete():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = created_todo_obj
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session_delete
        
        try:
            delete_response = client.delete(
                f"/todos/{todo_id}",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert delete_response.status_code == 200
            assert delete_response.json()["ok"] is True
        finally:
            app.dependency_overrides.clear()
    
    def test_multiple_todos_workflow(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试多个待办事项的工作流程"""
        todo1 = models.Todo(
            id=1,
            user_id=1,
            title="待办1",
            completed=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        todo2 = models.Todo(
            id=2,
            user_id=1,
            title="待办2",
            completed=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        todo3 = models.Todo(
            id=3,
            user_id=1,
            title="待办3",
            completed=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        # 获取所有待办
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [todo1, todo2, todo3]
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            list_response = client.get(
                "/todos",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert list_response.status_code == 200
            todos = list_response.json()
            assert len(todos) == 3
            
            # 验证已完成和未完成的待办
            completed_count = sum(1 for todo in todos if todo["completed"])
            assert completed_count == 1
        finally:
            app.dependency_overrides.clear()


# ========== 测试用户隔离 ==========

class TestTodosUserIsolation:
    """测试待办事项用户隔离"""
    
    def test_users_cannot_access_others_todos(
        self,
        client,
        mock_user
    ):
        """测试用户无法访问其他用户的待办"""
        # 用户1的待办
        user1_todo = models.Todo(
            id=1,
            user_id=1,
            title="用户1的待办",
            completed=False,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        # 用户2尝试访问用户1的待办
        user2 = MagicMock()
        user2.id = 2
        user2.email = "user2@example.com"
        
        async def override_get_current_user():
            return user2
        
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
            # 用户2尝试切换用户1的待办状态
            response = client.patch(
                "/todos/1",
                headers={"Authorization": "Bearer token2"}
            )
            
            # 应该返回 404，因为查询时已经过滤了 user_id
            assert response.status_code == 404
            
            # 用户2尝试删除用户1的待办
            response = client.delete(
                "/todos/1",
                headers={"Authorization": "Bearer token2"}
            )
            
            # 删除接口是幂等的：查不到也返回成功
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

