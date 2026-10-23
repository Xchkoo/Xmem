import json
import re
from openai import OpenAI

from ..config import settings


# def _get_client() -> OpenAI:
#     if settings.llm_provider == "deepseek":
#         base_url = settings.llm_api_url or "https://api.deepseek.com"
#         return OpenAI(api_key=settings.llm_api_key, base_url=base_url)
#     if settings.llm_provider == "mimo":
#         base_url = settings.llm_api_url or "https://api.xiaomimimo.com/v1/chat/completions"
#         return OpenAI(api_key=settings.llm_api_key, base_url=base_url)
#     if setting.llm_provider 
#     if not settings.llm_api_key:
#         raise ValueError("LLM_API_KEY 未配置")

def _get_client() -> OpenAI:
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置")

    if settings.llm_provider == "deepseek":
        base_url = settings.llm_api_url or "https://api.deepseek.com"
    elif settings.llm_provider == "mimo":
        base_url = settings.llm_api_url or "https://api.xiaomimimo.com/v1/"
    else:
        raise ValueError(
            f"不支持的 LLM_PROVIDER: {settings.llm_provider!r}，"
            "支持的值为 deepseek、mimo"
        )
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=base_url,
    )


def _unwrap_json_content(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) > 2:
            text = "\n".join(lines[1:-1]).strip()
    return text


def generate_note_summary(note_text: str) -> str:
    client = _get_client()
    prompt = (
        "你是笔记整理助手。请基于用户笔记内容输出简洁总结，要求："
        "1) 使用中文；2) 用 Markdown 列表呈现要点；3) 保留关键事实与行动项；"
        "4) 不要输出任何额外说明。"
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": note_text},
        ],
        stream=False,
    )
    return response.choices[0].message.content.strip()


def _normalize_todo_title(text: str) -> str:
    """规范化待办标题用于匹配。"""
    return re.sub(r"\s+", "", text or "").strip()


def _strip_completed_markers(text: str) -> tuple[str, bool]:
    """移除完成标记并返回完成状态。"""
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*[-*•+]\s*", "", cleaned)
    cleaned = re.sub(r"^\s*\d+[.)、]\s*", "", cleaned)
    completed = False
    patterns = [
        r"^\s*\[x\]\s*",
        r"^\s*\[X\]\s*",
        r"^\s*✅\s*",
        r"^\s*✔\s*",
        r"^\s*√\s*",
        r"^\s*×\s*",
        r"^\s*✗\s*",
        r"^\s*❌\s*",
        r"^\s*☑\s*",
        r"^\s*[（(【\[]\s*已完成\s*[】)\]]\s*",
        r"\s*[（(【\[]\s*已完成\s*[】)\]]\s*$",
    ]
    for pattern in patterns:
        if re.search(pattern, cleaned):
            completed = True
            cleaned = re.sub(pattern, "", cleaned).strip()
    if not completed and "已完成" in cleaned and "未完成" not in cleaned:
        completed = True
        cleaned = cleaned.replace("已完成", "").strip()
    return cleaned, completed


def _extract_completed_titles(note_text: str) -> list[str]:
    """从笔记文本中提取已完成条目标题。"""
    titles: list[str] = []
    for raw in note_text.splitlines():
        text = raw.strip()
        if not text:
            continue
        cleaned, completed = _strip_completed_markers(text)
        if completed and cleaned:
            titles.append(cleaned)
    return titles


def _extract_todo_item(item: object) -> tuple[str, bool | None]:
    """从 AI 返回条目中提取标题与完成状态。"""
    title = ""
    completed: bool | None = None
    if isinstance(item, str):
        title = item.strip()
    elif isinstance(item, dict):
        for key in ("completed", "done", "finished", "is_completed", "is_done", "已完成"):
            if key in item:
                value = item.get(key)
                if isinstance(value, bool):
                    completed = value
                elif isinstance(value, str):
                    completed = value.strip().lower() in ("true", "yes", "y", "1", "是", "已完成")
                elif isinstance(value, int):
                    completed = bool(value)
                break
        for key in ("title", "task", "todo", "text", "content", "name", "事项", "任务", "待办"):
            value = item.get(key)
            if value:
                title = str(value).strip()
                break
        if not title and len(item) == 1:
            value = next(iter(item.values()))
            title = str(value).strip()
    elif isinstance(item, list) and item:
        title = str(item[0]).strip()
    if title:
        title, completed_marker = _strip_completed_markers(title)
        if completed is None:
            completed = completed_marker
        else:
            completed = completed or completed_marker
    return title, completed


def generate_note_todos(note_text: str) -> list[dict[str, object]]:
    """生成待办条目列表，包含完成状态。"""
    client = _get_client()
    prompt = (
        "你是待办提取助手。请从用户笔记中提取待办事项，输出 JSON 数组，"
        "数组元素为对象，字段包含 title 和 completed。要求："
        "1) 不要输出解释；2) 标题简洁明确；3) 至多 10 条；"
        "4) 如果没有待办，返回空数组；"
        "5) 含明确时间与动作的安排也视为待办（例如：2月3号出发去机场）；"
        "6) 只要文本看起来像条目，就尽量转成待办，不要过度筛选。"
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": note_text},
        ],
        stream=False,
    )
    content = _unwrap_json_content(response.choices[0].message.content)
    try:
        data = json.loads(content)
    except ValueError:
        data = content
    if isinstance(data, dict):
        for key in ("todos", "items", "tasks", "list"):
            if key in data:
                data = data[key]
                break
    todo_items: list[dict[str, object]] = []
    if isinstance(data, list):
        for item in data:
            title, completed = _extract_todo_item(item)
            if title:
                todo_items.append({"title": title, "completed": bool(completed)})
    elif isinstance(data, str):
        for raw in data.splitlines():
            text = raw.strip().lstrip("-*").strip()
            if text.startswith("[ ]"):
                text = text[3:].strip()
            if text:
                title, completed = _strip_completed_markers(text)
                if title:
                    todo_items.append({"title": title, "completed": completed})
    if not todo_items:
        for raw in note_text.splitlines():
            text = raw.strip().lstrip("-*").strip()
            if text.startswith("[ ]"):
                text = text[3:].strip()
            if not text:
                continue
            title, completed = _strip_completed_markers(text)
            if title:
                todo_items.append({"title": title, "completed": completed})
        if not todo_items:
            text = note_text.strip().lstrip("-*").strip()
            if text.startswith("[ ]"):
                text = text[3:].strip()
            if text:
                title, completed = _strip_completed_markers(text)
                if title:
                    todo_items.append({"title": title, "completed": completed})
    completed_titles = _extract_completed_titles(note_text)
    completed_norms = [_normalize_todo_title(title) for title in completed_titles]
    if completed_norms:
        existing_norms = {_normalize_todo_title(str(item.get("title", "")).strip()) for item in todo_items}
        for item in todo_items:
            if item.get("completed"):
                continue
            title = str(item.get("title", "")).strip()
            normalized_title = _normalize_todo_title(title)
            for completed_title in completed_norms:
                if not completed_title:
                    continue
                if normalized_title in completed_title or completed_title in normalized_title:
                    item["completed"] = True
                    break
        for title, normalized_title in zip(completed_titles, completed_norms):
            if not normalized_title:
                continue
            if normalized_title in existing_norms:
                continue
            if any(
                normalized_title in exist or exist in normalized_title
                for exist in existing_norms
            ):
                continue
            todo_items.append({"title": title, "completed": True})
    if not isinstance(todo_items, list):
        raise ValueError("AI 返回的待办格式无效")
    return todo_items[:10]


def generate_ledger_monthly_summary(ledger_text: str) -> str:
    """生成记账月度总结。"""
    client = _get_client()
    prompt = (
        "你是记账分析助手。请基于用户当月记账记录输出简洁总结，要求："
        "1) 使用中文；2) 用 Markdown 列表呈现 3-6 条要点；"
        "3) 包含主要支出结构与可能的节省建议；"
        "4) 不要输出任何额外说明。"
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": ledger_text},
        ],
        stream=False,
    )
    return response.choices[0].message.content.strip()


def generate_chat_response(messages: list[dict], context_text: str | None = None) -> str:
    """
    生成通用对话回复（支持可选上下文）。
    Args:
        messages: 对话消息列表，包含 role 与 content
        context_text: 额外上下文文本，将作为 system 或 user 前缀提示
    Returns:
        模型回复文本
    """
    client = _get_client()
    sys_prompt = (
        "你是智能助手，回答需简洁准确，使用中文。若提供了上下文，请充分利用上下文信息回答。"
    )
    msgs: list[dict] = [{"role": "system", "content": sys_prompt}]
    if context_text and context_text.strip():
        msgs.append({"role": "system", "content": f"以下是用户提供的上下文，请在回答时参考：\n{context_text.strip()}"})
    # 追加用户消息序列
    for m in messages:
        role = m.get("role") or "user"
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        msgs.append({"role": role, "content": content})
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        stream=False,
    )
    return response.choices[0].message.content.strip()
