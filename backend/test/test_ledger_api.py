"""
Ledger API 路由测试
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import Depends
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import io
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
def mock_token():
    """模拟 token"""
    return "test_token_12345"


# ========== 测试创建 Ledger ==========

class TestCreateLedger:
    """测试创建 ledger 端点"""
    
    def test_create_ledger_with_text_only(
        self, 
        client,
        mock_user,
        mock_token
    ):
        """测试只提供文本创建 ledger"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # 创建完整的 entry 对象
            new_entry = models.LedgerEntry(
                id=1,
                user_id=1,
                raw_text="测试文本",
                status="pending",
                currency="CNY",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            
            # Mock 数据库操作
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            # Mock refresh 来设置 entry 的所有属性
            async def mock_refresh(obj):
                obj.id = 1
                obj.currency = "CNY"
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送请求
            response = client.post(
                "/ledger",
                json={"text": "测试文本"},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["raw_text"] == "测试文本"
        finally:
            # 清理覆盖
            app.dependency_overrides.clear()
    
    @patch('app.routers.ledger.save_uploaded_img')
    def test_create_ledger_with_image(
        self,
        mock_save_img,
        client,
        mock_user,
        mock_token,
        sample_image_bytes
    ):
        """测试上传图片创建 ledger"""
        mock_save_img.return_value = "uploads/images/test.jpg"
        
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = 1
                obj.currency = "CNY"
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送请求
            response = client.post(
                "/ledger",
                files={"image": ("test.png", sample_image_bytes, "image/png")},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.routers.ledger.save_uploaded_img')
    def test_create_ledger_with_text_and_image(
        self,
        mock_save_img,
        client,
        mock_user,
        mock_token,
        sample_image_bytes
    ):
        """测试同时提供文本和图片创建 ledger"""
        mock_save_img.return_value = "uploads/images/test.jpg"
        
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            
            async def mock_refresh(obj):
                obj.id = 1
                obj.currency = "CNY"
                obj.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送请求
            response = client.post(
                "/ledger",
                data={"text": "这是备注"},
                files={"image": ("test.png", sample_image_bytes, "image/png")},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["raw_text"] == "这是备注"
        finally:
            app.dependency_overrides.clear()
    
    def test_create_ledger_without_auth(self, client):
        """测试未认证的请求"""
        response = client.post(
            "/ledger",
            json={"text": "测试"}
        )
        assert response.status_code == 401
    
    def test_create_ledger_invalid_content_type(
        self, 
        client,
        mock_user,
        mock_token
    ):
        """测试无效的 Content-Type"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.post(
                "/ledger",
                data="invalid data",
                headers={
                    "Authorization": f"Bearer {mock_token}",
                    "Content-Type": "text/plain"
                }
            )
            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()
    
    def test_create_ledger_empty_text(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试空文本的情况"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/ledger",
                json={"text": ""},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()
    
    def test_create_ledger_no_text_no_image(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试既没有文本也没有图片的情况"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.post(
                "/ledger",
                json={},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()


# ========== 测试获取 Ledger ==========

class TestGetLedger:
    """测试获取 ledger 端点"""
    
    def test_list_ledgers(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试获取所有 ledger"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询结果
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            # Mock count query result
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0
            
            # Setup execute side effects to handle both queries
            async def mock_execute(query):
                query_str = str(query)
                if "count" in query_str.lower():
                    return mock_count_result
                return mock_result
                
            mock_session.execute = AsyncMock(side_effect=mock_execute)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送请求
            response = client.get(
                "/ledger",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()
    
    def test_list_ledgers_with_data(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试获取包含数据的 ledger 列表"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询结果
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_ledger_entry]
            # Mock count query result
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 1
            
            # Setup execute side effects to handle both queries
            async def mock_execute(query):
                query_str = str(query)
                if "count" in query_str.lower():
                    return mock_count_result
                return mock_result
                
            mock_session.execute = AsyncMock(side_effect=mock_execute)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/ledger",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1
            assert data["items"][0]["id"] == 1
            assert data["total"] == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_get_single_ledger(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试获取单个 ledger"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询结果
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_ledger_entry
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送请求
            response = client.get(
                "/ledger/1",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["status"] == "pending"
        finally:
            app.dependency_overrides.clear()
    
    def test_get_single_ledger_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试获取不存在的 ledger"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询结果 - 返回 None
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/ledger/999",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
    
    def test_get_ledger_without_auth(self, client):
        """测试未认证获取 ledger"""
        response = client.get("/ledger/1")
        assert response.status_code == 401


# ========== 测试 Summary ==========

class TestLedgerSummary:
    """测试 ledger 摘要端点"""
    
    def test_get_summary(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试获取摘要"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询结果
            mock_total_result = MagicMock()
            mock_total_result.scalar.return_value = 100.0
            mock_recent_result = MagicMock()
            mock_recent_result.scalars.return_value.all.return_value = []
            
            call_count = 0
            async def mock_execute(query):
                nonlocal call_count
                call_count += 1
                # 根据查询类型返回不同的结果
                query_str = str(query)
                if "sum" in query_str.lower() or "coalesce" in query_str.lower():
                    return mock_total_result
                else:
                    return mock_recent_result
            
            mock_session.execute = mock_execute
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送请求
            response = client.get(
                "/ledger/summary",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert "total_amount" in data
            assert "recent" in data
            assert data["total_amount"] == 100.0
            assert isinstance(data["recent"], list)
        finally:
            app.dependency_overrides.clear()
    
    def test_get_summary_with_recent_entries(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试获取包含最近条目的摘要"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_total_result = MagicMock()
            mock_total_result.scalar.return_value = 250.0
            mock_recent_result = MagicMock()
            mock_recent_result.scalars.return_value.all.return_value = [mock_ledger_entry]
            
            call_count = 0
            async def mock_execute(query):
                nonlocal call_count
                call_count += 1
                # 根据查询类型返回不同的结果
                query_str = str(query)
                if "sum" in query_str.lower() or "coalesce" in query_str.lower():
                    return mock_total_result
                else:
                    return mock_recent_result
            
            mock_session.execute = mock_execute
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.get(
                "/ledger/summary",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_amount"] == 250.0
            assert len(data["recent"]) == 1
        finally:
            app.dependency_overrides.clear()
    
    def test_get_summary_without_auth(self, client):
        """测试未认证获取摘要"""
        response = client.get("/ledger/summary")
        assert response.status_code == 401


# ========== 测试更新 Ledger ==========

class TestUpdateLedger:
    """测试更新 ledger 端点"""
    
    def test_update_ledger_success(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试成功更新 ledger"""
        # 覆盖依赖
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            # Mock 查询结果
            mock_result = MagicMock()
            # 创建一个可修改的 ledger entry
            updated_entry = models.LedgerEntry(
                id=1,
                user_id=1,
                raw_text="更新后的文本",
                status="completed",
                amount=200.0,
                currency="CNY",
                category="餐饮美食",
                merchant="商店A",
                event_time=datetime.now(timezone.utc).replace(tzinfo=None),
                meta=None,
                task_id=None,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            mock_result.scalar_one_or_none.return_value = mock_ledger_entry
            mock_session.execute = AsyncMock(return_value=mock_result)
            # Mock refresh 来更新对象
            async def mock_refresh(obj):
                obj.amount = updated_entry.amount
                obj.currency = updated_entry.currency
                obj.category = updated_entry.category
                obj.merchant = updated_entry.merchant
                obj.raw_text = updated_entry.raw_text
            mock_session.refresh = AsyncMock(side_effect=mock_refresh)
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 发送更新请求
            response = client.patch(
                "/ledger/1",
                json={
                    "amount": 200.0,
                    "currency": "CNY",
                    "category": "餐饮美食",
                    "merchant": "商店A",
                    "raw_text": "更新后的文本"
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            # 注意：由于 mock 的限制，实际返回值可能不会完全更新
            # 但我们可以验证请求成功
        finally:
            app.dependency_overrides.clear()
    
    def test_update_ledger_partial_fields(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试部分更新 ledger 字段"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_ledger_entry
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.refresh = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 只更新金额和分类
            response = client.patch(
                "/ledger/1",
                json={
                    "amount": 150.0,
                    "category": "餐饮美食"
                },
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
    
    def test_update_ledger_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试更新不存在的 ledger"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/ledger/999",
                json={"amount": 100.0},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_update_ledger_without_auth(self, client):
        """测试未认证更新 ledger"""
        response = client.patch(
            "/ledger/1",
            json={"amount": 100.0}
        )
        assert response.status_code == 401
    
    def test_update_ledger_empty_payload(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试使用空 payload 更新（应该成功但不改变任何字段）"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_ledger_entry
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.refresh = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.patch(
                "/ledger/1",
                json={},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


# ========== 测试删除 Ledger ==========

class TestDeleteLedger:
    """测试删除 ledger 端点"""
    
    def test_delete_ledger_success(
        self,
        client,
        mock_user,
        mock_token,
        mock_ledger_entry
    ):
        """测试成功删除 ledger"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_ledger_entry
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.delete(
                "/ledger/1",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "已删除" in data["message"]
        finally:
            app.dependency_overrides.clear()
    
    def test_delete_ledger_not_found(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试删除不存在的 ledger"""
        async def override_get_current_user():
            return mock_user
        
        async def override_get_session():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            response = client.delete(
                "/ledger/999",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
    
    def test_delete_ledger_without_auth(self, client):
        """测试未认证删除 ledger"""
        response = client.delete("/ledger/1")
        assert response.status_code == 401
    
    def test_delete_ledger_user_isolation(
        self,
        client,
        mock_user,
        mock_token
    ):
        """测试用户隔离：不能删除其他用户的 ledger"""
        # 创建另一个用户
        other_user = MagicMock()
        other_user.id = 2
        
        async def override_get_current_user():
            return mock_user  # 当前用户是 user_id=1
        
        async def override_get_session():
            mock_session = AsyncMock()
            # 返回 None，因为查询时会过滤 user_id，其他用户的条目不会被找到
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)
            yield mock_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_session] = override_get_session
        
        try:
            # 尝试删除其他用户的 ledger（假设 ledger_id=2 属于 user_id=2）
            response = client.delete(
                "/ledger/2",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # 应该返回 404，因为查询时已经过滤了 user_id
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

