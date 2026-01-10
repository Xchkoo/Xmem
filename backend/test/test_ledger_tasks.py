"""
Ledger Celery 任务测试
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone

from app.tasks.ledger_tasks import (
    merge_text_and_analyze,
    wrap_analyze_text_with_entry_id,
    update_ledger_entry,
    analyze_ledger_text
)
from app import models


# ========== 测试合并文本并分析 ==========

class TestMergeTextAndAnalyze:
    """测试合并文本并分析任务"""
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    def test_merge_text_with_original(self, mock_analyze):
        """测试合并 OCR 文本和原始文本"""
        # Mock LLM 分析结果
        mock_analyze.return_value = {
            "amount": 100.0,
            "currency": "CNY",
            "category": "餐饮",
            "merchant": None,
            "event_time": "2024-01-15T10:30:00Z",
            "meta": {
                "description": "测试描述"
            }
        }
        
        # 执行任务
        result = merge_text_and_analyze(
            ocr_text="OCR提取的文本",
            original_text="用户备注",
            entry_id=1
        )
        
        # 验证
        assert result["_entry_id"] == 1
        assert result["_original_text"] == "用户备注"
        assert "备注remark" in result["meta"]["raw_text"]
        assert "OCR提取的文本" in result["meta"]["raw_text"]
        assert result["amount"] == 100.0
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    def test_merge_text_without_original(self, mock_analyze):
        """测试只有 OCR 文本的情况"""
        mock_analyze.return_value = {
            "amount": 50.0,
            "currency": "CNY",
            "category": "交通",
            "merchant": None,
            "event_time": "2024-01-15T10:30:00Z",
            "meta": {
                "description": "OCR描述"
            }
        }
        
        result = merge_text_and_analyze(
            ocr_text="OCR提取的文本",
            original_text=None,
            entry_id=1
        )
        
        assert result["_entry_id"] == 1
        assert result["meta"]["raw_text"] == "OCR提取的文本"
        assert result["amount"] == 50.0
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    def test_merge_text_empty_ocr(self, mock_analyze):
        """测试 OCR 文本为空的情况"""
        mock_analyze.return_value = {
            "amount": 0.0,
            "currency": "CNY",
            "category": "未分类",
            "meta": {}
        }
        
        result = merge_text_and_analyze(
            ocr_text="",
            original_text="只有备注",
            entry_id=1
        )
        
        assert result["_entry_id"] == 1
        assert "备注remark" in result["meta"]["raw_text"]


# ========== 测试包装分析任务 ==========

class TestWrapAnalyzeText:
    """测试包装分析文本任务"""
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    def test_wrap_analyze_text_success(self, mock_analyze):
        """测试成功包装分析任务"""
        mock_analyze.return_value = {
            "amount": 200.0,
            "currency": "CNY",
            "category": "购物",
            "meta": {}
        }
        
        result = wrap_analyze_text_with_entry_id("今天买了200元的东西", 1)
        
        assert result["_entry_id"] == 1
        assert result["amount"] == 200.0
        mock_analyze.assert_called_once_with("今天买了200元的东西")
    
    @patch('app.tasks.ledger_tasks.analyze_ledger_text')
    def test_wrap_analyze_text_with_meta(self, mock_analyze):
        """测试包含 meta 信息的分析结果"""
        mock_analyze.return_value = {
            "amount": 150.0,
            "currency": "USD",
            "category": "娱乐",
            "meta": {
                "description": "测试描述",
                "model": "deepseek-chat"
            }
        }
        
        result = wrap_analyze_text_with_entry_id("测试文本", 2)
        
        assert result["_entry_id"] == 2
        assert result["meta"]["description"] == "测试描述"


# ========== 测试更新 Ledger 条目 ==========

class TestUpdateLedgerEntry:
    """测试更新 ledger 条目任务"""
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_update_entry_success(self, mock_session_local):
        """测试成功更新条目"""
        # Mock 数据库会话
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # 准备分析结果
        ai_result = {
            "amount": 200.0,
            "currency": "CNY",
            "category": "餐饮美食",
            "merchant": None,
            "event_time": "2024-01-15T10:30:00Z",
            "meta": {
                "description": "测试描述",
                "model": "deepseek-chat"
            }
        }
        
        # 执行任务
        result = update_ledger_entry(ai_result, entry_id=1)
        
        # 验证
        assert result["status"] == "completed"
        assert result["entry_id"] == 1
        assert mock_entry.amount == 200.0
        assert mock_entry.currency == "CNY"
        assert mock_entry.category == "餐饮美食"
        assert mock_entry.status == "completed"
        assert mock_entry.meta["description"] == "测试描述"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_update_entry_with_entry_id_in_result(self, mock_session_local):
        """测试从 ai_result 中提取 entry_id"""
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=2,
            user_id=1,
            raw_text="",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        # ai_result 中包含 _entry_id
        ai_result = {
            "_entry_id": 2,
            "amount": 300.0,
            "currency": "CNY",
            "category": "餐饮",
            "meta": {}
        }
        
        result = update_ledger_entry(ai_result)
        
        assert result["status"] == "completed"
        assert result["entry_id"] == 2
        assert mock_entry.amount == 300.0
        # 验证 _entry_id 已被移除
        assert "_entry_id" not in ai_result
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_update_entry_not_found(self, mock_session_local):
        """测试条目不存在的情况"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_session
        
        ai_result = {"amount": 100.0}
        
        with pytest.raises(ValueError, match="账本条目.*不存在"):
            update_ledger_entry(ai_result, entry_id=999)
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_update_entry_with_raw_text_in_meta(self, mock_session_local):
        """测试使用 meta 中的 raw_text 更新"""
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        ai_result = {
            "amount": 100.0,
            "meta": {
                "raw_text": "合并后的完整文本"
            }
        }
        
        update_ledger_entry(ai_result, entry_id=1)
        
        assert mock_entry.raw_text == "合并后的完整文本"
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_update_entry_invalid_event_time(self, mock_session_local):
        """测试无效的 event_time 格式"""
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session_local.return_value = mock_session
        
        ai_result = {
            "amount": 100.0,
            "event_time": "invalid-time-format",
            "meta": {}
        }
        
        # 应该使用当前时间作为默认值
        result = update_ledger_entry(ai_result, entry_id=1)
        
        assert result["status"] == "completed"
        assert mock_entry.event_time is not None
    
    @patch('app.tasks.ledger_tasks.SyncSessionLocal')
    def test_update_entry_error_handling(self, mock_session_local):
        """测试错误处理和状态回退"""
        mock_session = MagicMock()
        mock_entry = models.LedgerEntry(
            id=1,
            user_id=1,
            raw_text="",
            status="processing"
        )
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_session.commit.side_effect = Exception("数据库错误")
        mock_session_local.return_value = mock_session
        
        ai_result = {"amount": 100.0}
        
        with pytest.raises(Exception):
            update_ledger_entry(ai_result, entry_id=1)
        
        # 验证状态被更新为 failed
        assert mock_entry.status == "failed"
        # 验证 rollback 被调用
        mock_session.rollback.assert_called_once()


# ========== 测试 LLM 分析 ==========

class TestAnalyzeLedgerText:
    """测试 LLM 分析任务"""
    
    @patch('app.tasks.ledger_tasks.OpenAI')
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_success(self, mock_settings, mock_openai_class):
        """测试成功分析文本"""
        # Mock 配置
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "test_key"
        mock_settings.llm_api_url = "https://api.deepseek.com"
        
        # Mock OpenAI 客户端
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock API 响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"amount": 100, "currency": "CNY", "category": "餐饮美食", "description": "午餐", "event_time": "2024-01-15T12:00:00Z"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = analyze_ledger_text("今天午餐花费100元")
        
        assert result["amount"] == 100.0
        assert result["currency"] == "CNY"
        assert result["category"] == "餐饮美食"
        assert result["event_time"] == "2024-01-15T12:00:00Z"
        assert "meta" in result
    
    @patch('app.tasks.ledger_tasks.OpenAI')
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_with_markdown_code_block(self, mock_settings, mock_openai_class):
        """测试 LLM 返回包含 markdown 代码块的情况"""
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "test_key"
        mock_settings.llm_api_url = "https://api.deepseek.com"
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '```json\n{"amount": 50, "currency": "CNY", "category": "交通"}\n```'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = analyze_ledger_text("交通费50元")
        
        assert result["amount"] == 50.0
        assert result["currency"] == "CNY"
    
    @pytest.mark.parametrize(
        "response_content, expected_amount, expected_currency",
        [
            (
                '{"amount": "1,234.50元", "currency": "cny (人民币)", "category": "餐饮美食", "event_time": "2024-01-15T12:00:00Z"}',
                1234.5,
                "CNY",
            ),
            (
                '{"amount": -88.8, "currency": "usd ", "category": "餐饮美食", "event_time": "2024-01-15T12:00:00Z"}',
                88.8,
                "USD",
            ),
            (
                '{"amount": 0, "currency": "RMB", "category": "餐饮美食", "event_time": "2024-01-15T12:00:00Z"}',
                None,
                "CNY",
            ),
            (
                '{"amount": "abc", "currency": 123, "category": "餐饮美食", "event_time": "2024-01-15T12:00:00Z"}',
                None,
                "CNY",
            ),
            (
                '{"amount": NaN, "currency": "EUR", "category": "餐饮美食", "event_time": "2024-01-15T12:00:00Z"}',
                None,
                "EUR",
            ),
        ],
    )
    @patch('app.tasks.ledger_tasks.OpenAI')
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_dirty_amount_currency(
        self,
        mock_settings,
        mock_openai_class,
        response_content,
        expected_amount,
        expected_currency,
    ):
        """测试 LLM 返回脏 amount/currency 时仍能健壮返回"""
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "test_key"
        mock_settings.llm_api_url = "https://api.deepseek.com"
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = response_content
        mock_client.chat.completions.create.return_value = mock_response
        
        result = analyze_ledger_text("测试文本")
        
        assert "amount" in result
        assert "currency" in result
        assert "category" in result
        assert "event_time" in result
        assert "meta" in result
        
        assert result["amount"] == expected_amount
        assert result["currency"] == expected_currency
    
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_no_provider(self, mock_settings):
        """测试未配置 LLM provider"""
        mock_settings.llm_provider = None
        
        result = analyze_ledger_text("测试文本")
        
        assert result["amount"] is None
        assert result["category"] == "其他"
        assert "LLM 未配置" in result["meta"]["note"]
    
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_no_api_key(self, mock_settings):
        """测试未配置 API key"""
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = None
        
        result = analyze_ledger_text("测试文本")
        
        assert result["amount"] is None
        assert result["category"] == "其他"
        assert "LLM_API_KEY 未配置" in result["meta"]["note"]
    
    @patch('app.tasks.ledger_tasks.OpenAI')
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_invalid_json(self, mock_settings, mock_openai_class):
        """测试 LLM 返回无效 JSON"""
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "test_key"
        mock_settings.llm_api_url = "https://api.deepseek.com"
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "这不是有效的 JSON"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = analyze_ledger_text("测试文本")
        
        assert result["amount"] is None
        assert result["category"] == "其他"
        assert "LLM API 调用失败" in result["meta"]["note"]
    
    @patch('app.tasks.ledger_tasks.OpenAI')
    @patch('app.tasks.ledger_tasks.settings')
    def test_analyze_ledger_text_invalid_time_format(self, mock_settings, mock_openai_class):
        """测试无效的时间格式"""
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "test_key"
        mock_settings.llm_api_url = "https://api.deepseek.com"
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"amount": 100, "event_time": "invalid-time"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = analyze_ledger_text("测试")
        
        # 应该使用当前 UTC 时间
        assert result["event_time"] is not None
        assert "T" in result["event_time"]
        assert result["event_time"].endswith("Z")

