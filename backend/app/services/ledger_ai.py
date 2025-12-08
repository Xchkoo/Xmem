from datetime import datetime


async def analyze(text: str) -> dict:
    # 占位：可替换为真实大模型调用
    return {
        "amount": None,
        "currency": "CNY",
        "category": "未分类",
        "merchant": None,
        "event_time": datetime.utcnow(),
        "meta": {"model": "stub"},
    }

