# config.py - 配置文件
# 项目配置信息，包括 API 密钥和新闻源配置

# ==================== API 密钥配置 ====================

# NewsAPI 密钥
# 1. 访问 https://newsapi.org/ 注册免费账号
# 2. 获取 API Key（免费版 100 次/天）
NEWSAPI_KEY = "your_newsapi_key_here"

# GNews API 密钥（国内可访问）
# 1. 访问 https://gnews.io/ 注册免费账号
# 2. 获取 API Key（免费版 100 次/天）
GNEWS_API_KEY = "your_gnews_api_key_here"

# 百度NLP API 密钥（中文情感分析）
# 1. 访问 https://ai.baidu.com/ 登录百度账号
# 2. 创建应用，选择"自然语言处理"
# 3. 获取 API Key 和 Secret Key
# 免费额度: 5万次/天
BAIDU_API_KEY = "your_baidu_api_key_here"
BAIDU_SECRET_KEY = "your_baidu_secret_key_here"

# ==================== 搜索配置 ====================

# 目标公司名称：IF椰子水（泰国品牌）
# 多关键词组合，平衡相关性和覆盖率
COMPANY_KEYWORDS = [
    '"IF" coconut water',
    'IF coconut drink',
    'IF beverage Thailand',
    'IF 椰子水',
    'IF椰汁',
    'coconut water recall IF',
    'IF brand coconut',
]

# 主关键词
PRIMARY_KEYWORD = '"IF" coconut water'

# 新闻语言
LANGUAGE = "en"

# 每个新闻源获取的最大数量
MAX_RESULTS_PER_SOURCE = 20

# ==================== RSS 订阅源配置 ====================

# RSS 订阅源列表（仅保留验证可用的源）
# IF椰子水是小众品牌，公开RSS中极少直接出现，行业源提供相关背景新闻
RSS_SOURCES = [
    # === 饮料/食品行业（已验证可用）===
    {"name": "BevNet", "url": "https://www.bevnet.com/feed/"},
    {"name": "BevNet News", "url": "https://www.bevnet.com/news/feed/"},
    {"name": "Food Dive", "url": "https://www.fooddive.com/feeds/news/"},
    {"name": "Food Safety News", "url": "https://www.foodsafetynews.com/feed/"},
    {"name": "Grocery Dive", "url": "https://www.grocerydive.com/feeds/news/"},

    # === 国内财经/消费 ===
    {"name": "36kr", "url": "https://36kr.com/feed"},

    # === 国际食品/饮料 ===
    {"name": "Just Food", "url": "https://www.just-food.com/feed/"},
]

# ==================== 风险关键词库 ====================

RISK_KEYWORDS = {
    "劳工风险": [
        "strike", "labor dispute", "worker protest", "union", "wage",
        "employee rights", "working conditions", "layoff", "firing",
        "discrimination", "harassment", "safety incident", "injury",
        "罢工", "劳资纠纷", "员工抗议", "工会", "工资", "裁员"
    ],
    "法律风险": [
        "lawsuit", "litigation", "fine", "penalty", "violation",
        "regulatory", "compliance", "court", "legal action", "settlement",
        "investigation", "sanction", "breach", "fraud", "诉讼", "罚款"
    ],
    "供应链风险": [
        "supply chain", "shortage", "recall", "contamination",
        "quality issue", "supplier", "raw material", "production halt",
        "factory closure", "inventory", "distribution", "物流", "召回",
        "adulterated", "watered down", "sugar added", "quality control",
        "掺水", "掺糖", "质量问题", "品控", "检测不合格"
    ],
    "财务风险": [
        "bankruptcy", "debt", "loss", "profit decline", "revenue drop",
        "stock plunge", "rating downgrade", "default", "financial crisis",
        "破产", "亏损", "股价下跌", "债务"
    ],
    "声誉风险": [
        "scandal", "boycott", "complaint", "negative review",
        "social media backlash", "PR crisis", "controversy", "criticism",
        "丑闻", "抵制", "负面评价", "公关危机",
        "adulteration", "fake", "fraud", "misleading", "debunk",
        "掺水", "掺糖", "造假", "虚假宣传", "辟谣", "澄清"
    ],
    "环境风险": [
        "pollution", "environmental", "climate", "sustainability",
        "carbon", "emission", "waste", "deforestation", "环保", "污染"
    ]
}

# ==================== 风险评分阈值 ====================

RISK_THRESHOLDS = {
    "low": 30,
    "medium": 60,
    "high": 80,
    "critical": 100
}

# ==================== 新闻去重配置 ====================

# 去重相似度阈值（0-1，越高越严格）
DEDUPLICATION_THRESHOLD = 0.8

# 去重时考虑的字段权重
DEDUPLICATION_WEIGHTS = {
    "title": 0.6,
    "content": 0.3,
    "source": 0.1
}
