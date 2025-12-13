"""
生成假记账数据脚本
用于测试统计界面

使用方法:
    python generate_fake_ledger_data.py [count]
    python generate_fake_ledger_data.py --email user@example.com [count]
    python generate_fake_ledger_data.py --user-id 1 [count]

参数:
    count: 可选，要生成的数据条数，默认 200 条
    --email: 可选，通过邮箱指定用户
    --user-id: 可选，通过用户ID指定用户
    如果不指定用户，默认使用第一个用户
"""
import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, select, Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from app.config import settings
from app.constants import LEDGER_CATEGORIES

# 创建独立的 Base，避免导入 app.db 时创建异步引擎
Base = declarative_base()

# 直接定义模型，避免导入 app.models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    user_name = Column(String(64), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    raw_text = Column(Text, nullable=False)
    amount = Column(Float, nullable=True)
    currency = Column(String(16), default="CNY")
    category = Column(String(64), nullable=True)
    merchant = Column(String(128), nullable=True)
    event_time = Column(DateTime, nullable=True)
    meta = Column(JSON, nullable=True)
    status = Column(String(16), default="pending", nullable=False)
    task_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


# 创建同步数据库引擎
try:
    sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    sync_engine = create_engine(sync_db_url, pool_pre_ping=True)
    SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
except Exception as e:
    if "psycopg2" in str(e).lower() or "ModuleNotFoundError" in str(type(e).__name__):
        print("错误: 缺少 psycopg2-binary 模块")
        print("请运行以下命令安装依赖:")
        print("  pip install psycopg2-binary")
        print("或者如果使用 uv:")
        print("  uv pip install psycopg2-binary")
        sys.exit(1)
    raise


# 商家名称列表
MERCHANTS = {
    "餐饮美食": ["肯德基", "麦当劳", "星巴克", "海底捞", "必胜客", "真功夫", "永和大王", "沙县小吃", "兰州拉面", "黄焖鸡米饭"],
    "服装装扮": ["优衣库", "ZARA", "H&M", "Nike", "Adidas", "李宁", "安踏", "太平鸟", "海澜之家", "森马"],
    "日用百货": ["沃尔玛", "家乐福", "大润发", "永辉超市", "华润万家", "7-Eleven", "便利蜂", "罗森", "全家", "屈臣氏"],
    "家居家装": ["宜家", "红星美凯龙", "居然之家", "欧派", "索菲亚", "全友家居", "顾家家居", "林氏木业", "芝华仕", "慕思"],
    "数码电器": ["京东", "天猫", "苏宁易购", "国美", "小米", "华为", "苹果", "联想", "戴尔", "惠普"],
    "运动户外": ["迪卡侬", "探路者", "Columbia", "The North Face", "安踏", "李宁", "特步", "361度", "匹克", "鸿星尔克"],
    "美容美发": ["屈臣氏", "丝芙兰", "完美日记", "花西子", "自然堂", "欧莱雅", "资生堂", "兰蔻", "雅诗兰黛", "SK-II"],
    "母婴亲子": ["孩子王", "爱婴室", "贝因美", "美赞臣", "飞鹤", "合生元", "帮宝适", "好奇", "花王", "大王"],
    "宠物": ["宠物医院", "宠物店", "皇家", "冠能", "比瑞吉", "麦顿", "顽皮", "路斯", "好主人", "疯狂小狗"],
    "交通出行": ["滴滴出行", "高德打车", "曹操出行", "T3出行", "首汽约车", "地铁", "公交", "出租车", "共享单车", "高铁"],
    "爱车养车": ["中石化", "中石油", "壳牌", "美孚", "嘉实多", "途虎养车", "汽车4S店", "洗车店", "停车场", "ETC"],
    "住房物业": ["物业费", "水电费", "燃气费", "网费", "房租", "房贷", "装修", "家具", "家电", "维修"],
    "酒店旅游": ["携程", "去哪儿", "飞猪", "同程", "途牛", "马蜂窝", "Airbnb", "如家", "汉庭", "7天"],
    "文化休闲": ["电影院", "KTV", "游戏厅", "书店", "咖啡厅", "茶楼", "酒吧", "夜店", "演唱会", "展览"],
    "教育培训": ["新东方", "学而思", "猿辅导", "作业帮", "VIPKID", "英语培训", "钢琴课", "舞蹈班", "美术班", "编程课"],
    "医疗健康": ["医院", "药店", "体检中心", "牙科", "眼科", "中医", "按摩", "理疗", "健身房", "瑜伽馆"],
    "生活服务": ["洗衣店", "干洗店", "修鞋店", "配钥匙", "开锁", "搬家", "保洁", "家政", "快递", "外卖"],
    "公共服务": ["政府", "税务局", "工商局", "车管所", "银行", "邮局", "电信", "移动", "联通", "广电"],
    "商业服务": ["广告公司", "设计公司", "咨询公司", "律师事务所", "会计师事务所", "翻译公司", "印刷", "摄影", "婚庆", "装修公司"],
    "公益捐赠": ["红十字会", "慈善机构", "希望工程", "壹基金", "腾讯公益", "支付宝公益", "水滴筹", "轻松筹", "爱心捐赠", "志愿者"],
    "互助保障": ["保险", "互助", "保障", "理赔", "报销", "医疗险", "意外险", "重疾险", "寿险", "车险"],
    "投资理财": ["股票", "基金", "债券", "银行理财", "P2P", "余额宝", "理财通", "支付宝", "微信支付", "投资"],
    "保险": ["中国人保", "中国平安", "中国人寿", "太平洋保险", "新华保险", "泰康保险", "友邦保险", "安联保险", "阳光保险", "大地保险"],
    "信用借还": ["信用卡", "花呗", "借呗", "白条", "分期", "贷款", "还款", "利息", "手续费", "逾期"],
    "充值缴费": ["话费", "流量", "电费", "水费", "燃气费", "网费", "有线电视", "物业费", "停车费", "会员费"],
    "其他": ["其他支出", "杂项", "未分类", "临时", "应急", "备用", "零用", "小费", "红包", "礼金"]
}

# 金额范围（按分类）
AMOUNT_RANGES = {
    "餐饮美食": (15, 200),
    "服装装扮": (50, 2000),
    "日用百货": (10, 500),
    "家居家装": (100, 10000),
    "数码电器": (200, 15000),
    "运动户外": (50, 3000),
    "美容美发": (30, 1000),
    "母婴亲子": (50, 2000),
    "宠物": (20, 800),
    "交通出行": (5, 500),
    "爱车养车": (50, 2000),
    "住房物业": (100, 5000),
    "酒店旅游": (200, 5000),
    "文化休闲": (30, 500),
    "教育培训": (100, 5000),
    "医疗健康": (50, 3000),
    "生活服务": (20, 500),
    "公共服务": (10, 1000),
    "商业服务": (200, 10000),
    "公益捐赠": (10, 1000),
    "互助保障": (100, 5000),
    "投资理财": (1000, 50000),
    "保险": (200, 10000),
    "信用借还": (100, 50000),
    "充值缴费": (20, 500),
    "其他": (10, 1000)
}


def generate_fake_ledger_entry(user_id: int, days_ago: int) -> LedgerEntry:
    """生成一个假记账条目"""
    # 随机选择分类
    category = random.choice(LEDGER_CATEGORIES)
    
    # 根据分类选择商家
    merchants = MERCHANTS.get(category, ["商家"])
    merchant = random.choice(merchants)
    
    # 根据分类生成金额
    min_amount, max_amount = AMOUNT_RANGES.get(category, (10, 1000))
    amount = round(random.uniform(min_amount, max_amount), 2)
    
    # 生成时间（过去 days_ago 天内的随机时间）
    now = datetime.now(timezone.utc)
    days_ago_dt = now - timedelta(days=days_ago)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    event_time = days_ago_dt.replace(hour=random_hours, minute=random_minutes, second=0, microsecond=0)
    
    # 生成原始文本
    raw_text = f"{merchant} {category} {amount}元"
    
    # 创建记账条目
    entry = LedgerEntry(
        user_id=user_id,
        raw_text=raw_text,
        amount=amount,
        currency="CNY",
        category=category,
        merchant=merchant,
        event_time=event_time.replace(tzinfo=None),  # 数据库存储 naive datetime
        status="completed",
        meta={
            "description": raw_text,
            "generated": True
        },
        created_at=event_time.replace(tzinfo=None),
        updated_at=event_time.replace(tzinfo=None)
    )
    
    return entry


def main():
    """主函数"""
    # 解析命令行参数
    user_email = None
    user_id = None
    count = 200
    list_users = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--email" or arg == "-e":
            if i + 1 < len(sys.argv):
                user_email = sys.argv[i + 1]
                i += 2
            else:
                print("错误: --email 需要提供邮箱地址")
                return
        elif arg == "--user-id" or arg == "-u" or arg == "--id":
            if i + 1 < len(sys.argv):
                try:
                    user_id = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print("错误: --user-id 需要提供数字ID")
                    return
            else:
                print("错误: --user-id 需要提供用户ID")
                return
        elif arg == "--list-users" or arg == "-l":
            list_users = True
            i += 1
        else:
            # 尝试解析为数字（count）
            try:
                count = int(arg)
                i += 1
            except ValueError:
                # 如果不是选项，可能是旧格式的邮箱（兼容性）
                if "@" in arg:
                    user_email = arg
                    i += 1
                    if i < len(sys.argv):
                        try:
                            count = int(sys.argv[i])
                            i += 1
                        except ValueError:
                            pass
                else:
                    print(f"错误: 无法识别的参数: {arg}")
                    print("使用方法:")
                    print("  python generate_fake_ledger_data.py [count]")
                    print("  python generate_fake_ledger_data.py --email user@example.com [count]")
                    print("  python generate_fake_ledger_data.py --user-id 1 [count]")
                    print("  python generate_fake_ledger_data.py --list-users")
                    return
    
    session: Session = SyncSessionLocal()
    
    try:
        # 如果只是列出用户，则列出后退出
        if list_users:
            users = session.query(User).all()
            if not users:
                print("数据库中没有用户")
                return
            
            print("所有用户列表:")
            print("-" * 60)
            print(f"{'ID':<5} {'Email':<30} {'用户名':<20}")
            print("-" * 60)
            for user in users:
                user_name = user.user_name or "(未设置)"
                print(f"{user.id:<5} {user.email:<30} {user_name:<20}")
            print("-" * 60)
            return
        
        # 获取用户
        user = None
        if user_id:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"错误: 用户ID {user_id} 不存在")
                return
        elif user_email:
            user = session.query(User).filter(User.email == user_email).first()
            if not user:
                print(f"错误: 用户邮箱 {user_email} 不存在")
                return
        else:
            # 使用第一个用户
            user = session.query(User).first()
            if not user:
                print("错误: 数据库中没有用户，请先创建用户")
                return
        
        print(f"为用户 (ID: {user.id}, Email: {user.email}) 生成 {count} 条假记账数据...")
        
        # 生成数据（过去 6 个月）
        entries = []
        for i in range(count):
            # 随机分布在过去 180 天内
            days_ago = random.randint(0, 180)
            entry = generate_fake_ledger_entry(user.id, days_ago)
            entries.append(entry)
        
        # 批量插入
        session.add_all(entries)
        session.commit()
        
        print(f"成功生成 {count} 条记账数据！")
        print(f"时间范围: 过去 180 天")
        print(f"分类分布:")
        category_counts = {}
        for entry in entries:
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} 条")
        
    except Exception as e:
        session.rollback()
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()

