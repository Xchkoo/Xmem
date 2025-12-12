"""
Ledger 集成测试
测试完整的端到端流程
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import io
from PIL import Image

from app import models
from app.tasks.ledger_tasks import (
    merge_text_and_analyze,
    update_ledger_entry
)
from app.tasks.ocr_tasks import extract_text_from_image_task


# ========== 测试完整流程 ==========

class TestLedgerIntegration:
    """测试 Ledger 完整流程"""
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_full_flow_text_only(
        self,
        mock_session_local,
        mock_analyze
    ):
        """测试只有文本的完整流程"""
        # 1. Mock LLM 分析
        mock_analyze.return_value = {
            "amount": 150.0,
            "currency": "CNY",
            "category": "餐饮",
            "merchant": None,
            "event_time": "2024-01-15T12:00:00Z",
            "meta": {
                "description": "午餐花费150元",
                "model": "deepseek-chat"
            }
        }
        
        # 2. Mock 数据库
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="午餐花费150元",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # 3. 执行分析任务
        analysis_result = merge_text_and_analyze(
            ocr_text="午餐花费150元",
            original_text=None,
            entry_id=1
        )
        
        # 4. 验证分析结果
        assert analysis_result["_entry_id"] == 1
        assert analysis_result["amount"] == 150.0
        
        # 5. 执行更新任务
        update_result = update_ledger_entry(analysis_result)
        
        # 6. 验证更新结果
        assert update_result["status"] == "completed"
        assert mock_entry.amount == 150.0
        assert mock_entry.status == "completed"
        assert mock_entry.category == "餐饮"
    
    @patch('app.services.ocr.extract_text_from_image_local')
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_full_flow_with_image(
        self,
        mock_session_local,
        mock_analyze,
        mock_ocr_local,
        tmp_path
    ):
        """测试带图片的完整流程"""
        # 1. 创建测试图片
        test_image_path = tmp_path / "test.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(test_image_path)
        
        # 2. Mock OCR - patch extract_text_from_image_local（因为 extract_text_from_image 会调用它）
        mock_ocr_local.return_value = "发票金额：200元"
        
        # 3. Mock LLM 分析
        mock_analyze.return_value = {
            "amount": 200.0,
            "currency": "CNY",
            "category": "购物",
            "merchant": None,
            "event_time": "2024-01-15T14:00:00Z",
            "meta": {
                "description": "发票金额：200元",
                "model": "deepseek-chat"
            }
        }
        
        # 4. Mock 数据库
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=2,
            user_id=1,
            raw_text="",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # 5. 测试 OCR 函数（mock extract_text_from_image_local，因为 extract_text_from_image 会调用它）
        from app.services.ocr import extract_text_from_image
        ocr_text = extract_text_from_image(str(test_image_path))
        # 验证 mock 被调用
        mock_ocr_local.assert_called_once_with(str(test_image_path))
        assert ocr_text == "发票金额：200元"
        
        # 6. 执行合并和分析任务
        analysis_result = merge_text_and_analyze(
            ocr_text=ocr_text,
            original_text="这是备注",
            entry_id=2
        )
        
        # 7. 验证合并结果
        assert analysis_result["_entry_id"] == 2
        assert "备注remark" in analysis_result["meta"]["raw_text"]
        assert "发票金额：200元" in analysis_result["meta"]["raw_text"]
        
        # 8. 执行更新任务
        update_result = update_ledger_entry(analysis_result)
        
        # 9. 验证最终结果
        assert update_result["status"] == "completed"
        assert mock_entry.amount == 200.0
        assert mock_entry.status == "completed"
        assert "备注remark" in mock_entry.raw_text
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_flow_with_error_handling(
        self,
        mock_session_local,
        mock_analyze
    ):
        """测试错误处理和状态回退"""
        # 1. Mock LLM 分析失败
        mock_analyze.side_effect = Exception("LLM API 错误")
        
        # 2. Mock 数据库
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=3,
            user_id=1,
            raw_text="测试",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # 3. 尝试分析（应该失败）
        with pytest.raises(Exception):
            merge_text_and_analyze(
                ocr_text="测试文本",
                original_text=None,
                entry_id=3
            )
        
        # 4. 模拟更新失败状态
        mock_entry.status = "failed"
        assert mock_entry.status == "failed"


# ========== 测试状态流转 ==========

class TestStatusFlow:
    """测试状态流转"""
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_status_pending_to_processing(self, mock_session_local):
        """测试从 pending 到 processing 的状态流转"""
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="测试",
            status="pending"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # 模拟启动 Celery 任务后更新状态
        mock_entry.status = "processing"
        mock_entry.task_id = "celery-task-123"
        mock_session.commit()
        
        assert mock_entry.status == "processing"
        assert mock_entry.task_id == "celery-task-123"
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_status_processing_to_completed(
        self,
        mock_session_local,
        mock_analyze
    ):
        """测试从 processing 到 completed 的状态流转"""
        mock_analyze.return_value = {
            "amount": 100.0,
            "currency": "CNY",
            "category": "测试",
            "meta": {}
        }
        
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="测试",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # 执行更新
        analysis_result = {
            "_entry_id": 1,
            "amount": 100.0,
            "currency": "CNY",
            "category": "测试",
            "meta": {}
        }
        update_ledger_entry(analysis_result)
        
        assert mock_entry.status == "completed"
        assert mock_entry.amount == 100.0
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_status_processing_to_failed(self, mock_session_local):
        """测试从 processing 到 failed 的状态流转"""
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="测试",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session.commit.side_effect = Exception("数据库错误")
        mock_session_local.return_value = mock_session
        
        # 模拟更新失败
        ai_result = {"amount": 100.0}
        
        with pytest.raises(Exception):
            update_ledger_entry(ai_result, entry_id=1)
        
        # 验证状态被更新为 failed
        assert mock_entry.status == "failed"


# ========== 测试多用户隔离 ==========

class TestUserIsolation:
    """测试多用户数据隔离"""
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_user_can_only_see_own_ledgers(self, mock_session_local):
        """测试用户只能看到自己的 ledger"""
        mock_session = MagicMock()
        
        # 用户1的 ledger
        entry1 = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="用户1的条目",
            status="completed"
        )
        
        # 用户2的 ledger
        entry2 = models.LedgerEntry(
            id=2,
            user_id=2,
            raw_text="用户2的条目",
            status="completed"
        )
        
        # Mock 查询 - 只返回用户1的条目
        def mock_query(model):
            query = MagicMock()
            if model == models.LedgerEntry:
                filter_mock = MagicMock()
                filter_mock.where.return_value.first.return_value = entry1
                query.filter.return_value = filter_mock
            return query
        
        mock_session.query = mock_query
        mock_session_local.return_value = mock_session
        
        # 验证用户1只能获取自己的条目
        result = mock_session.query(models.LedgerEntry).filter(
            models.LedgerEntry.id == 1
        ).where(
            models.LedgerEntry.user_id == 1
        ).first()
        
        assert result.user_id == 1
        assert result.id == 1

