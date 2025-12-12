"""
Auth 集成测试
测试完整的认证流程
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


# ========== 测试完整认证流程 ==========

class TestAuthIntegration:
    """测试完整的认证流程"""
    
    def test_full_auth_flow_register_login_me(
        self,
        client,
        mock_user
    ):
        """测试完整的认证流程：注册 -> 登录 -> 获取用户信息"""
        # 1. 注册新用户
        async def override_get_session_register():
            mock_session = AsyncMock()
            # 第一次查询：邮箱不存在
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
        
        app.dependency_overrides[get_session] = override_get_session_register
        
        try:
            register_response = client.post(
                "/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "hashed_password_123",
                    "user_name": "New User"
                }
            )
            
            assert register_response.status_code == 200
            user_data = register_response.json()
            assert user_data["email"] == "newuser@example.com"
            user_id = user_data["id"]
        finally:
            app.dependency_overrides.clear()
        
        # 2. 登录
        new_user = MagicMock()
        new_user.id = user_id
        new_user.email = "newuser@example.com"
        new_user.user_name = "New User"
        new_user.hashed_password = "hashed_password_123"
        new_user.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        with patch('app.routers.auth.verify_password', return_value=True):
            async def override_get_session_login():
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.first.return_value = new_user
                mock_session.execute = AsyncMock(return_value=mock_result)
                yield mock_session
            
            app.dependency_overrides[get_session] = override_get_session_login
            
            try:
                login_response = client.post(
                    "/auth/login",
                    json={
                        "email": "newuser@example.com",
                        "password": "hashed_password_123"
                    }
                )
                
                assert login_response.status_code == 200
                token_data = login_response.json()
                assert "access_token" in token_data
                access_token = token_data["access_token"]
            finally:
                app.dependency_overrides.clear()
        
        # 3. 使用 token 获取用户信息
        async def override_get_current_user_me():
            return new_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user_me
        
        try:
            me_response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            assert me_response.status_code == 200
            me_data = me_response.json()
            assert me_data["email"] == "newuser@example.com"
            assert me_data["id"] == user_id
        finally:
            app.dependency_overrides.clear()
    
    def test_full_auth_flow_with_password_change(
        self,
        client,
        mock_user
    ):
        """测试包含修改密码的完整流程"""
        # 1. 登录
        with patch('app.routers.auth.verify_password', return_value=True):
            async def override_get_session_login():
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.first.return_value = mock_user
                mock_session.execute = AsyncMock(return_value=mock_result)
                yield mock_session
            
            app.dependency_overrides[get_session] = override_get_session_login
            
            try:
                login_response = client.post(
                    "/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "hashed_password_123"
                    }
                )
                
                assert login_response.status_code == 200
                access_token = login_response.json()["access_token"]
            finally:
                app.dependency_overrides.clear()
        
        # 2. 修改密码
        with patch('app.routers.auth.verify_password', return_value=True):
            async def override_get_current_user():
                return mock_user
            
            async def override_get_session_change():
                mock_session = AsyncMock()
                mock_session.commit = AsyncMock()
                yield mock_session
            
            app.dependency_overrides[get_current_user] = override_get_current_user
            app.dependency_overrides[get_session] = override_get_session_change
            
            try:
                change_response = client.post(
                    "/auth/change-password",
                    json={
                        "old_password": "hashed_password_123",
                        "new_password": "hashed_new_password"
                    },
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                assert change_response.status_code == 200
                assert "成功" in change_response.json()["message"]
            finally:
                app.dependency_overrides.clear()
        
        # 3. 使用新密码登录（验证密码已更新）
        updated_user = MagicMock()
        updated_user.id = 1
        updated_user.email = "test@example.com"
        updated_user.hashed_password = "hashed_new_password"
        
        with patch('app.routers.auth.verify_password', return_value=True):
            async def override_get_session_new_login():
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.first.return_value = updated_user
                mock_session.execute = AsyncMock(return_value=mock_result)
                yield mock_session
            
            app.dependency_overrides[get_session] = override_get_session_new_login
            
            try:
                new_login_response = client.post(
                    "/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "hashed_new_password"
                    }
                )
                
                assert new_login_response.status_code == 200
                assert "access_token" in new_login_response.json()
            finally:
                app.dependency_overrides.clear()


# ========== 测试错误场景 ==========

class TestAuthErrorScenarios:
    """测试认证错误场景"""
    
    def test_register_then_login_with_wrong_password(
        self,
        client
    ):
        """测试注册后使用错误密码登录"""
        # 1. 注册
        async def override_get_session_register():
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
        
        app.dependency_overrides[get_session] = override_get_session_register
        
        try:
            register_response = client.post(
                "/auth/register",
                json={
                    "email": "user@example.com",
                    "password": "correct_password"
                }
            )
            assert register_response.status_code == 200
        finally:
            app.dependency_overrides.clear()
        
        # 2. 使用错误密码登录
        registered_user = MagicMock()
        registered_user.id = 1
        registered_user.email = "user@example.com"
        registered_user.hashed_password = "correct_password"
        
        with patch('app.routers.auth.verify_password', return_value=False):
            async def override_get_session_login():
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.first.return_value = registered_user
                mock_session.execute = AsyncMock(return_value=mock_result)
                yield mock_session
            
            app.dependency_overrides[get_session] = override_get_session_login
            
            try:
                login_response = client.post(
                    "/auth/login",
                    json={
                        "email": "user@example.com",
                        "password": "wrong_password"
                    }
                )
                
                assert login_response.status_code == 401
                assert "错误" in login_response.json()["detail"]
            finally:
                app.dependency_overrides.clear()
    
    def test_duplicate_registration(
        self,
        client,
        mock_user
    ):
        """测试重复注册"""
        async def override_get_session():
            mock_session = AsyncMock()
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
                    "password": "password"
                }
            )
            
            assert response.status_code == 400
            assert "已被注册" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ========== 测试用户隔离 ==========

class TestUserIsolation:
    """测试用户数据隔离"""
    
    def test_users_cannot_access_others_data(
        self,
        client,
        mock_user
    ):
        """测试用户无法访问其他用户的数据"""
        # 创建两个用户
        user1 = MagicMock()
        user1.id = 1
        user1.email = "user1@example.com"
        user1.user_name = "User 1"
        user1.hashed_password = "password1"
        user1.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        user2 = MagicMock()
        user2.id = 2
        user2.email = "user2@example.com"
        user2.user_name = "User 2"
        user2.hashed_password = "password2"
        user2.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # 用户1登录
        with patch('app.routers.auth.verify_password', return_value=True):
            async def override_get_session():
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.first.return_value = user1
                mock_session.execute = AsyncMock(return_value=mock_result)
                yield mock_session
            
            app.dependency_overrides[get_session] = override_get_session
            
            try:
                login_response = client.post(
                    "/auth/login",
                    json={
                        "email": "user1@example.com",
                        "password": "password1"
                    }
                )
                
                assert login_response.status_code == 200
                token1 = login_response.json()["access_token"]
            finally:
                app.dependency_overrides.clear()
        
        # 用户1获取自己的信息
        async def override_get_current_user():
            return user1
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            me_response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token1}"}
            )
            
            assert me_response.status_code == 200
            me_data = me_response.json()
            assert me_data["id"] == 1
            assert me_data["email"] == "user1@example.com"
        finally:
            app.dependency_overrides.clear()

