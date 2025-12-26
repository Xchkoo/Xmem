"""
Auth API 路由测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.main import app
from app import models
from app.db import get_session
from app.auth import get_current_user, verify_password, create_access_token


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
    user.user_name = "Test User"
    user.hashed_password = "hashed_password_123"
    user.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    return user


@pytest.fixture
def mock_token():
    """模拟 token"""
    return "test_token_12345"


# ========== 测试注册 ==========

class TestRegister:
    """测试注册端点"""
    
    def test_register_success(
        self,
        client,
        mock_user
    ):
        """测试成功注册"""
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询 - 邮箱不存在
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = 1
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "hashed_password_123",
                    "user_name": "New User"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "newuser@example.com"
            assert data["user_name"] == "New User"
            assert "id" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_register_duplicate_email(
        self,
        client,
        mock_user
    ):
        """测试重复邮箱注册"""
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询 - 邮箱已存在
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "hashed_password_123",
                    "user_name": "Test User"
                }
            )
            
            assert response.status_code == 400
            assert "已被注册" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_register_without_user_name(
        self,
        client
    ):
        """测试不提供用户名注册"""
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = 1
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "hashed_password_123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "newuser@example.com"
        finally:
            app.dependency_overrides.clear()

    def test_register_empty_password(self, client):
        """测试空密码注册"""
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock email check (not exists)
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "",
                    "user_name": "New User"
                }
            )
            assert response.status_code == 400
            assert "密码不能为空" in response.json()["detail"]

            response = client.post(
                "/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "   ",
                    "user_name": "New User"
                }
            )
            assert response.status_code == 400
            assert "密码不能为空" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ========== 测试登录 ==========

class TestLogin:
    """测试登录端点"""
    
    @patch('app.routers.auth.verify_password')
    def test_login_success(
        self,
        mock_verify_password,
        client,
        mock_user,
        mock_token
    ):
        """测试成功登录"""
        mock_verify_password.return_value = True
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "hashed_password_123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.routers.auth.verify_password')
    def test_login_wrong_password(
        self,
        mock_verify_password,
        client,
        mock_user
    ):
        """测试错误密码登录"""
        mock_verify_password.return_value = False
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_user
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrong_password"
                }
            )
            
            assert response.status_code == 401
            assert "错误" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_login_user_not_found(
        self,
        client
    ):
        """测试用户不存在"""
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "password"
                }
            )
            
            assert response.status_code == 401
            assert "错误" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ========== 测试获取当前用户 ==========

class TestGetMe:
    """测试获取当前用户端点"""
    
    def test_get_me_success(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试成功获取当前用户信息"""
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["user_name"] == "Test User"
            assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_get_me_without_auth(self, client):
        """测试未认证获取用户信息"""
        response = client.get("/auth/me")
        assert response.status_code == 401


# ========== 测试修改密码 ==========

class TestChangePassword:
    """测试修改密码端点"""
    
    @patch('app.routers.auth.verify_password')
    def test_change_password_success(
        self,
        mock_verify_password,
        client,
        mock_user,
        mock_token
    ):
        """测试成功修改密码"""
        mock_verify_password.return_value = True
        
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "hashed_old_password",
                    "new_password": "hashed_new_password"
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "成功" in data["message"]
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.routers.auth.verify_password')
    def test_change_password_wrong_old_password(
        self,
        mock_verify_password,
        client,
        mock_user,
        mock_token
    ):
        """测试原密码错误"""
        mock_verify_password.return_value = False
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "wrong_password",
                    "new_password": "hashed_new_password"
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 400
            assert "原密码错误" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_change_password_without_auth(self, client):
        """测试未认证修改密码"""
        response = client.post(
            "/auth/change-password",
            json={
                "old_password": "old",
                "new_password": "new"
            }
        )
        assert response.status_code == 401

