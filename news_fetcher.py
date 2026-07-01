"""
news_fetcher.py - 新闻获取模块
支持多源聚合：NewsAPI + GNews + RSS订阅
包含智能去重机制
"""

import requests
import feedparser
import re
import json
import hashlib
import time
import signal
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from dateutil import parser as date_parser

from config import (
    NEWSAPI_KEY, GNEWS_API_KEY, COMPANY_KEYWORDS, PRIMARY_KEYWORD, LANGUAGE,
    MAX_RESULTS_PER_SOURCE, RSS_SOURCES, DEDUPLICATION_THRESHOLD
)


# ==================== 抽象基类 ====================

class BaseNewsSource(ABC):
    """新闻源抽象基类"""

    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    @abstractmethod
    def fetch(self, days_back: int = 30) -> List[Dict]:
        """获取新闻，返回统一格式的列表"""
        pass

    def _normalize_article(self, title: str, description: str = "",
                          content: str = "", url: str = "",
                          published_at: str = "", source: str = "") -> Dict:
        """统一文章格式"""
        return {
            "title": title.strip() if title else "",
            "description": description.strip() if description else "",
            "content": content.strip() if content else (description.strip() if description else ""),
            "url": url.strip() if url else "",
            "published_at": self._normalize_date(published_at),
            "source": source.strip() if source else self.name,
            "source_type": self.name,
            "fetched_at": datetime.now().isoformat()
        }

    def _normalize_date(self, date_str) -> str:
        """标准化日期格式为 ISO 8601"""
        if not date_str:
            return datetime.now().isoformat()

        try:
            if isinstance(date_str, datetime):
                return date_str.isoformat()
            # 尝试解析各种日期格式
            parsed = date_parser.parse(str(date_str))
            return parsed.isoformat()
        except Exception:
            return datetime.now().isoformat()


# ==================== NewsAPI 源 ====================

class NewsAPISource(BaseNewsSource):
    """NewsAPI 新闻源"""

    def __init__(self, api_key: str):
        super().__init__("NewsAPI")
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch(self, days_back: int = 30) -> List[Dict]:
        if self.api_key == "your_newsapi_key_here":
            print(f"[{self.name}] API key not set, skipping")
            return []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        all_articles = []
        keywords_to_search = COMPANY_KEYWORDS if isinstance(COMPANY_KEYWORDS, list) else [COMPANY_KEYWORDS]

        # 限制关键词数量，避免过多API调用
        search_keywords = keywords_to_search[:3]

        for keyword in search_keywords:
            params = {
                "q": keyword,
                "language": "en",
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "pageSize": min(MAX_RESULTS_PER_SOURCE, 10),  # 每个关键词少量结果
                "sortBy": "relevancy",
                "apiKey": self.api_key
            }

            try:
                response = requests.get(self.base_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok":
                    print(f"[{self.name}] API error for '{keyword}': {data.get('message', 'unknown error')}")
                    continue

                articles = data.get("articles", [])
                print(f"[{self.name}] Fetched {len(articles)} articles for '{keyword}'")

                for a in articles:
                    all_articles.append(self._normalize_article(
                        title=a.get("title", ""),
                        description=a.get("description", ""),
                        content=a.get("content", ""),
                        url=a.get("url", ""),
                        published_at=a.get("publishedAt", ""),
                        source=a.get("source", {}).get("name", "NewsAPI")
                    ))

            except requests.exceptions.RequestException as e:
                print(f"[{self.name}] Request failed for '{keyword}': {e}")
                continue
            except Exception as e:
                print(f"[{self.name}] Parse failed for '{keyword}': {e}")
                continue

        print(f"[{self.name}] Total articles fetched: {len(all_articles)}")
        return all_articles


# ==================== GNews 源 ====================

class GNewsSource(BaseNewsSource):
    """GNews API 新闻源（国内可访问）"""

    def __init__(self, api_key: str):
        super().__init__("GNews")
        self.api_key = api_key
        self.base_url = "https://gnews.io/api/v4/search"

    def fetch(self, days_back: int = 30) -> List[Dict]:
        if self.api_key == "your_gnews_api_key_here" or not self.api_key:
            print(f"[{self.name}] API key not set, skipping")
            return []

        all_articles = []
        keywords_to_search = COMPANY_KEYWORDS if isinstance(COMPANY_KEYWORDS, list) else [COMPANY_KEYWORDS]

        # 限制关键词数量
        search_keywords = keywords_to_search[:3]

        for keyword in search_keywords:
            params = {
                "q": keyword,
                "lang": "en",
                "max": min(MAX_RESULTS_PER_SOURCE, 10),
                "token": self.api_key
            }

            try:
                response = requests.get(self.base_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                articles = data.get("articles", [])
                print(f"[{self.name}] Fetched {len(articles)} articles for '{keyword}'")

                for a in articles:
                    source_name = a.get("source", {})
                    if isinstance(source_name, dict):
                        source_name = source_name.get("name", "GNews")

                    all_articles.append(self._normalize_article(
                        title=a.get("title", ""),
                        description=a.get("description", ""),
                        content=a.get("content", ""),
                        url=a.get("url", ""),
                        published_at=a.get("publishedAt", ""),
                        source=source_name
                    ))

            except requests.exceptions.RequestException as e:
                print(f"[{self.name}] Request failed for '{keyword}': {e}")
                continue
            except Exception as e:
                print(f"[{self.name}] Parse failed for '{keyword}': {e}")
                continue

        print(f"[{self.name}] Total articles fetched: {len(all_articles)}")
        return all_articles


# ==================== RSS 订阅源 ====================

class RSSSource(BaseNewsSource):
    """RSS 订阅源"""

    def __init__(self, name: str, rss_url: str):
        super().__init__(f"RSS-{name}")
        self.rss_url = rss_url
        self.source_name = name

    def fetch(self, days_back: int = 30) -> List[Dict]:
        try:
            # 解析 RSS feed
            feed = feedparser.parse(self.rss_url)

            if feed.get("bozo"):
                print(f"[{self.name}] RSS parse warning: {feed.get('bozo_exception', 'unknown issue')}")

            entries = feed.get("entries", [])
            cutoff_date = datetime.now() - timedelta(days=days_back)

            result = []
            for entry in entries:
                # 获取发布日期
                published = entry.get("published") or entry.get("updated") or ""

                # 过滤日期范围
                try:
                    if published:
                        pub_date = date_parser.parse(published)
                        if pub_date < cutoff_date:
                            continue
                except:
                    pass

                # 清理 HTML 标签
                description = self._clean_html(entry.get("summary", ""))
                content = self._clean_html(entry.get("description", ""))

                result.append(self._normalize_article(
                    title=entry.get("title", ""),
                    description=description,
                    content=content if content else description,
                    url=entry.get("link", ""),
                    published_at=published,
                    source=self.source_name
                ))

            print(f"[{self.name}] 成功获取 {len(result)} 条新闻")
            return result[:MAX_RESULTS_PER_SOURCE]

        except Exception as e:
            print(f"[{self.name}] Fetch failed: {e}")
            return []

    def _clean_html(self, raw_html: str) -> str:
        """清理 HTML 标签"""
        if not raw_html:
            return ""
        clean = re.sub(r'<[^>]+>', '', raw_html)
        return clean.strip()


# ==================== 演示数据源 ====================

class DemoSource(BaseNewsSource):
    """演示数据源 - 模拟椰子水掺水掺糖舆情危机事件"""

    def __init__(self):
        super().__init__("舆情监控模拟")

    def fetch(self, days_back: int = 30) -> List[Dict]:
        print(f"[{self.name}] Generating simulated 'IF coconut water' news data...")
        today = datetime.now()

        # IF椰子水综合舆情数据（25条模拟新闻，覆盖多维度）
        demo_articles = [
            # ========== 负面曝光阶段 ==========
            {
                "title": "曝IF椰子水涉嫌掺水掺糖！实测糖分超标",
                "description": "有消费者送检发现，热销品牌IF椰子水实际糖分含量远超标注，且检出添加糖浆成分，疑似并非100%纯椰子水。检测报告显示...",
                "published_at": (today - timedelta(days=2)).isoformat(),
                "source": "消费者报道",
                "url": "https://example.com/news/1"
            },
            {
                "title": "多家椰子水品牌被曝质量问题 IF也在列",
                "description": "媒体随机抽检10款椰子水产品，发现包括IF在内的多个品牌存在标签不实、添加剂超标等问题，引发消费者关注。",
                "published_at": (today - timedelta(days=2, hours=6)).isoformat(),
                "source": "食品安全网",
                "url": "https://example.com/news/2"
            },
            {
                "title": "网友实测：IF椰子水甜味不正常 疑加糖",
                "description": "多位网友在社交平台发文，表示IF椰子水口感过甜，与天然椰子水差异明显。有用户用血糖仪测试，发现饮用后血糖快速上升...",
                "published_at": (today - timedelta(days=2, hours=8)).isoformat(),
                "source": "微博热搜",
                "url": "https://example.com/news/3"
            },
            {
                "title": "IF椰子水引发行业震荡：掺水加糖成潜规则？",
                "description": "IF椰子水事件持续发酵，业内人士爆料，部分椰子水品牌为降低成本，采用浓缩还原加水加糖的方式生产，却标注100%纯椰子水。",
                "published_at": (today - timedelta(days=1, hours=12)).isoformat(),
                "source": "财经观察",
                "url": "https://example.com/news/4"
            },
            # ========== 舆论发酵阶段（危机扩散）==========
            {
                "title": "IF椰子水遭集体投诉 平台投诉量激增",
                "description": "各大电商平台数据显示，IF椰子水近一周投诉量环比增长300%，主要集中在'虚假宣传'、'质量问题'等方面。",
                "published_at": (today - timedelta(days=1)).isoformat(),
                "source": "电商观察",
                "url": "https://example.com/news/5"
            },
            {
                "title": "超市回应：已暂时下架IF椰子水相关产品",
                "description": "多家连锁超市表示，关注到相关舆情后，已暂时下架IF椰子水产品，等待品牌方和监管部门的进一步说明。",
                "published_at": (today - timedelta(days=1, hours=4)).isoformat(),
                "source": "零售资讯",
                "url": "https://example.com/news/6"
            },
            {
                "title": "专家解读：如何判断IF椰子水是否加糖",
                "description": "食品专家以IF椰子水为例指出，可通过查看配料表、营养成分表等判断。纯椰子水碳水化合物含量应在4-5g/100ml左右，过高可能添加了糖。",
                "published_at": (today - timedelta(days=1, hours=6)).isoformat(),
                "source": "健康时报",
                "url": "https://example.com/news/7"
            },
            # ========== 企业回应阶段（危机应对）==========
            {
                "title": "IF官方声明：产品符合标准 保留追责权利",
                "description": "IF品牌发布官方声明，称所有产品均通过正规检测，符合食品安全标准。对于不实传言，公司将保留追究法律责任的权利。",
                "published_at": (today - timedelta(hours=18)).isoformat(),
                "source": "品牌官方",
                "url": "https://example.com/news/8"
            },
            {
                "title": "IF公布第三方检测报告 否认掺水掺糖指控",
                "description": "IF椰子水公布SGS检测报告，显示产品未检出添加糖，符合100%椰子水标准。公司表示网传检测方法不科学。",
                "published_at": (today - timedelta(hours=14)).isoformat(),
                "source": "品牌公告",
                "url": "https://example.com/news/9"
            },
            {
                "title": "IF负责人回应：竞争对手恶意抹黑",
                "description": "IF中国区负责人表示，此次舆情是有组织有计划的恶意攻击，公司已掌握证据，将通过法律手段维护品牌声誉。",
                "published_at": (today - timedelta(hours=10)).isoformat(),
                "source": "财经专访",
                "url": "https://example.com/news/10"
            },
            # ========== 舆论反转阶段（争议持续）==========
            {
                "title": "消费者不买账：IF回应避重就轻",
                "description": "尽管IF发布检测报告，但部分消费者仍不买账。有网友质疑报告真实性，称自己的检测结果与品牌方公布的不一致。",
                "published_at": (today - timedelta(hours=8)).isoformat(),
                "source": "社交媒体",
                "url": "https://example.com/news/11"
            },
            {
                "title": "市场监管部门介入调查IF椰子水",
                "description": "据了解，相关市场监管部门已介入调查，将对市场上销售的椰子水产品进行抽检，结果将及时向社会公布。",
                "published_at": (today - timedelta(hours=6)).isoformat(),
                "source": "市场监管报",
                "url": "https://example.com/news/12"
            },
            {
                "title": "IF事件后：椰子水行业迎来洗牌 质量将成为关键",
                "description": "IF椰子水事件或将加速椰子水行业规范化进程。专家表示，随着消费者健康意识提升，产品质量将成为品牌竞争的核心。",
                "published_at": (today - timedelta(hours=4)).isoformat(),
                "source": "产业分析",
                "url": "https://example.com/news/13"
            },
            {
                "title": "IF椰子水海外销售是否受影响？",
                "description": "作为泰国进口品牌，IF椰子水在海外的销售情况引发关注。目前海外电商平台评论中已出现质疑声音。",
                "published_at": (today - timedelta(hours=2)).isoformat(),
                "source": "跨境观察",
                "url": "https://example.com/news/14"
            },
            {
                "title": "IF事件警示：如何选购真正的100%椰子水？",
                "description": "IF椰子水风波后，专家教你几招辨别真假椰子水：1.看配料表，纯椰子水应只有椰子水；2.看营养成分；3.选择知名品牌；4.注意口感...",
                "published_at": (today - timedelta(hours=1)).isoformat(),
                "source": "消费指南",
                "url": "https://example.com/news/15"
            },
            # ========== 追加10条：供应链+财务+ESG+劳工维度 ==========
            {
                "title": "IF椰子水泰国工厂被曝卫生不达标",
                "description": "泰媒报道称IF椰子水泰国工厂接受突击检查，发现生产线存在卫生隐患。IF官方尚未回应，消费者担忧产品质量。",
                "published_at": (today - timedelta(days=3)).isoformat(),
                "source": "Bangkok Post",
                "url": "https://example.com/news/16"
            },
            {
                "title": "IF椰子水供应商涉嫌非法用工 劳工组织发函",
                "description": "国际劳工组织关注IF椰子水供应链劳工权益问题，称收到泰国椰子农场存在克扣工资和强迫劳动的举报，呼吁品牌方彻查。",
                "published_at": (today - timedelta(days=4)).isoformat(),
                "source": "Reuters",
                "url": "https://example.com/news/17"
            },
            {
                "title": "IF椰子水2025年Q3财报：营收下滑15% 股价大跌",
                "description": "IF椰子水母公司发布2025年Q3财报，营收同比下降15%，毛利率收窄至28%。公司将此归因于椰子原材料价格上涨和品牌形象受损。",
                "published_at": (today - timedelta(days=5)).isoformat(),
                "source": "Bloomberg",
                "url": "https://example.com/news/18"
            },
            {
                "title": "IF椰子水被指过度包装 环保组织发起抗议",
                "description": "环保组织指出IF椰子水使用多层复合包装材料难以回收，呼吁品牌改用可降解包装。部分消费者在社交媒体发起#BoycottIF 话题。",
                "published_at": (today - timedelta(days=3, hours=12)).isoformat(),
                "source": "ESG Today",
                "url": "https://example.com/news/19"
            },
            {
                "title": "竞品趁虚而入：Vita Coco借IF危机抢占市场",
                "description": "IF椰子水陷入信任危机之际，竞品Vita Coco、Genius Juice等品牌加大营销力度，推出买一送一活动，市场份额显著增长。",
                "published_at": (today - timedelta(days=1, hours=8)).isoformat(),
                "source": "Food Dive",
                "url": "https://example.com/news/20"
            },
            {
                "title": "IF椰子水天猫旗舰店评分跌至4.2 差评激增",
                "description": "消费者在天猫平台大量差评，主要集中在甜味异常、口感变淡、保质期内变质等问题。IF椰子水旗舰店评分从4.8跌至4.2。",
                "published_at": (today - timedelta(days=1, hours=3)).isoformat(),
                "source": "电商观察",
                "url": "https://example.com/news/21"
            },
            {
                "title": "IF椰子水启动产品召回 涉事批次覆盖3个省份",
                "description": "IF椰子水发布产品召回公告，针对检测不合格的3个批次产品在全国范围内启动召回。预计涉及产品超过10万箱，直接损失或达千万。",
                "published_at": (today - timedelta(hours=5)).isoformat(),
                "source": "市场监管总局",
                "url": "https://example.com/news/22"
            },
            {
                "title": "泰国椰子水出口受挫 IF事件拖累泰国农业形象",
                "description": "IF椰子水事件引发连锁反应，泰国椰子水整体出口量受到影响。泰国农业部门紧急召开新闻发布会，强调泰国椰子质量标准不会因个别品牌受损。",
                "published_at": (today - timedelta(hours=3)).isoformat(),
                "source": "Thai PBS World",
                "url": "https://example.com/news/23"
            },
            {
                "title": "IF宣布更换CEO 前高管临危受命",
                "description": "IF椰子水宣布CEO辞职，由前NextFood亚太区总裁临危受命。新任CEO承诺90天内完成全面整改，重建消费者信任。",
                "published_at": (today - timedelta(hours=16)).isoformat(),
                "source": "财经观察",
                "url": "https://example.com/news/24"
            },
            {
                "title": "行业分析：IF椰子水危机对功能饮料市场的影响",
                "description": "分析师指出IF椰子水事件可能导致椰子水品类整体信任度下降，短期内消费者可能转向其他功能性饮品。预计椰子水市场规模将收缩12%-15%。",
                "published_at": (today).isoformat(),
                "source": "Beverage Daily",
                "url": "https://example.com/news/25"
            },
        ]

        return [self._normalize_article(
            title=a["title"],
            description=a["description"],
            content=a["description"],
            url=a["url"],
            published_at=a["published_at"],
            source=a["source"]
        ) for a in demo_articles]


# ==================== 新闻聚合器 ====================

class NewsAggregator:
    """
    新闻聚合器 - 管理多个新闻源
    功能：
    1. 从多个源并行获取新闻
    2. 智能去重
    3. 统一输出格式
    4. 缓存支持
    """

    def __init__(self, use_cache: bool = True):
        self.sources: List[BaseNewsSource] = []
        self.cache = NewsCache() if use_cache else None
        self._init_sources()

    def _init_sources(self):
        """初始化所有新闻源"""
        # NewsAPI（国外，需要Key）
        self.sources.append(NewsAPISource(NEWSAPI_KEY))

        # GNews（国外，国内可访问）
        self.sources.append(GNewsSource(GNEWS_API_KEY))

        # RSS 订阅源（包含国内财经媒体）
        for rss_config in RSS_SOURCES:
            self.sources.append(RSSSource(
                name=rss_config["name"],
                rss_url=rss_config["url"]
            ))

    def fetch_all(self, days_back: int = 30, deduplicate: bool = True, max_time: int = 300, use_cache: bool = True) -> List[Dict]:
        """
        从所有源获取新闻（带超时限制和缓存）

        Args:
            days_back: 获取多少天内的新闻
            deduplicate: 是否进行去重
            max_time: 最大执行时间（秒），默认300秒
            use_cache: 是否使用缓存

        Returns:
            统一格式的新闻列表
        """
        start_time = time.time()
        all_articles = []
        successful_sources = 0

        print(f"\n{'='*50}")
        print(f"Fetching data from {len(self.sources)} news sources...")
        print(f"Time limit: {max_time} seconds")
        print(f"Cache: {'Enabled' if use_cache and self.cache else 'Disabled'}")
        print(f"{'='*50}")

        for source in self.sources:
            # 检查是否超时
            elapsed = time.time() - start_time
            if elapsed > max_time:
                print(f"\n[!] Time limit ({max_time}s) reached, stopping fetch")
                break

            # 尝试从缓存获取
            if use_cache and self.cache:
                cached_articles = self.cache.get(source.name)
                if cached_articles is not None:
                    all_articles.extend(cached_articles)
                    successful_sources += 1
                    continue

            # 从源获取
            try:
                articles = source.fetch(days_back)
                if articles:
                    all_articles.extend(articles)
                    successful_sources += 1
                    # 保存到缓存
                    if use_cache and self.cache:
                        self.cache.set(source.name, articles)
            except Exception as e:
                print(f"[{source.name}] Error: {e}")

        print(f"\n{'='*50}")
        print(f"Successfully fetched from {successful_sources}/{len(self.sources)} sources")
        print(f"Total raw articles: {len(all_articles)}")
        print(f"{'='*50}\n")

        # 演示数据源（始终添加IF椰子水专项模拟数据作为补充）
        try:
            demo = DemoSource()
            demo_articles = demo.fetch(days_back)
            if demo_articles:
                all_articles.extend(demo_articles)
                print(f"[DemoSource] Added {len(demo_articles)} IF-specific simulated articles")
        except Exception as e:
            print(f"[DemoSource] Error: {e}")

        # 去重
        if deduplicate:
            all_articles = self._deduplicate(all_articles)

        # 按发布时间排序
        all_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        print(f"Final valid articles: {len(all_articles)}\n")
        return all_articles

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """
        智能去重 - 基于标题相似度

        策略：
        1. 计算标题相似度
        2. URL 完全相同的直接去重
        3. 相似度超过阈值认为是重复新闻
        """
        if not articles:
            return []

        unique_articles = []
        seen_urls = set()

        for article in articles:
            url = article.get("url", "")
            title = article.get("title", "")

            # URL 完全相同的跳过
            if url and url in seen_urls:
                continue
            seen_urls.add(url)

            # 检查标题相似度
            is_duplicate = False
            for existing in unique_articles:
                similarity = self._calculate_similarity(
                    title,
                    existing.get("title", "")
                )
                if similarity > DEDUPLICATION_THRESHOLD:
                    is_duplicate = True
                    # 合并来源信息（保留更多信息）
                    if article.get("source") != existing.get("source"):
                        existing["source"] = f"{existing['source']}, {article['source']}"
                    break

            if not is_duplicate:
                unique_articles.append(article)

        removed_count = len(articles) - len(unique_articles)
        if removed_count > 0:
            print(f"[Deduplication] Removed {removed_count} duplicate articles")

        return unique_articles

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度 (0-1)"""
        if not text1 or not text2:
            return 0.0

        # 预处理：小写、去除标点
        def clean(text):
            return re.sub(r'[^\w\s]', '', text.lower().strip())

        s1 = clean(text1)
        s2 = clean(text2)

        return SequenceMatcher(None, s1, s2).ratio()


# ==================== 品牌过滤器 ====================

# ==================== 缓存管理器 ====================

import json
import os
from datetime import datetime, timedelta

class NewsCache:
    """
    新闻缓存管理器 - 避免每次都从头抓取
    缓存有效期：4小时
    """

    CACHE_FILE = "news_cache.json"
    CACHE_TTL_HOURS = 4  # 缓存有效期4小时

    def __init__(self):
        self.cache_data = {}
        self._load_cache()

    def _load_cache(self):
        """加载缓存文件"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
            except Exception as e:
                print(f"[Cache] Load failed: {e}")
                self.cache_data = {}

    def _save_cache(self):
        """保存缓存文件"""
        try:
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Cache] Save failed: {e}")

    def get(self, source_name: str) -> Optional[List[Dict]]:
        """
        获取缓存数据

        Returns:
            缓存的文章列表，如果过期或不存在返回None
        """
        if source_name not in self.cache_data:
            return None

        cached = self.cache_data[source_name]
        cached_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))

        # 检查是否过期
        if datetime.now() - cached_time > timedelta(hours=self.CACHE_TTL_HOURS):
            print(f"[Cache] {source_name} cache expired")
            return None

        print(f"[Cache] {source_name} using cached data ({len(cached.get('articles', []))} articles)")
        return cached.get("articles", [])

    def set(self, source_name: str, articles: List[Dict]):
        """保存数据到缓存"""
        self.cache_data[source_name] = {
            "timestamp": datetime.now().isoformat(),
            "articles": articles
        }
        self._save_cache()

    def clear(self):
        """清除所有缓存"""
        self.cache_data = {}
        if os.path.exists(self.CACHE_FILE):
            os.remove(self.CACHE_FILE)
        print("[Cache] All cache cleared")


# ==================== 品牌过滤器 ====================

class BrandFilter:
    """
    品牌过滤器 - 确保只返回与IF品牌相关的新闻
    """

    # IF品牌相关关键词
    BRAND_KEYWORDS = [
        # 英文品牌词
        "if coconut water", "if brand", "if beverage", "if drinks", "if thailand",
        "if coconut", "if drink", "if product",
        # 中文品牌词
        "if 椰子水", "if椰汁", "if椰子", "if 泰国", "if椰子汁",
        "泰国 if", "if 椰汁", "if椰水",
        # 变体
        "i.f. coconut", "i.f coconut", "if-brand", "if_brand",
        # 通用椰子水泰国相关
        "coconut water thailand", "thai coconut water",
        # 椰子水品类
        "coconut water", "椰子水", "椰汁",
    ]

    # 饮料/食品行业垂直源（这些源中的椰子水/饮料新闻都相关）
    BEVERAGE_INDUSTRY_SOURCES = [
        "bevnet", "food dive", "food safety", "grocery dive",
        "just food", "beverage daily", "beverage industry",
        "36氪",
    ]

    # 品牌名精确匹配（避免匹配到英文单词"if"）
    EXACT_BRAND_PATTERNS = [
        r'\bIF\b',  # 大写IF作为独立单词
        r'if\s+coconut',  # if + coconut
        r'if\s+brand',  # if + brand
        r'泰国\s*if',  # 泰国if
        r'if\s*椰子',  # if椰子
        r'if\s*椰汁',  # if椰汁
    ]

    @classmethod
    def is_brand_related(cls, article: Dict) -> bool:
        """
        检查文章是否与IF品牌相关

        策略：
        1. IF品牌关键词直接匹配 → 保留
        2. 椰子水品类的任何新闻 → 保留
        3. 饮料行业垂直源中的饮料/食品新闻 → 保留（提供行业背景）
        """
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        content = article.get("content", "").lower()
        source = article.get("source", "").lower()
        source_type = article.get("source_type", "").lower()

        full_text = title + " " + description + " " + content

        # 1. 检查是否包含IF品牌关键词
        for keyword in cls.BRAND_KEYWORDS:
            if keyword.lower() in full_text:
                return True

        # 2. 使用正则表达式精确匹配IF品牌
        for pattern in cls.EXACT_BRAND_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                return True

        # 3. 椰子水品类的任何新闻（IF椰子水是主要品牌，品类新闻就是行业信号）
        if "coconut water" in full_text or "椰子水" in full_text or "椰汁" in full_text:
            return True

        # 4. 饮料行业源的饮料/食品新闻（提供行业监控背景）
        full_source = source + " " + source_type
        is_industry_source = any(
            s in full_source for s in cls.BEVERAGE_INDUSTRY_SOURCES
        )
        if is_industry_source:
            beverage_keywords = [
                "beverage", "drink", "coconut", "water", "food",
                "bottle", "hydration", "juice", "functional",
                "饮料", "饮品", "食品", "椰子", "瓶装", "果汁",
                "recall", "quality", "safety", "consumer",
            ]
            if any(kw in full_text for kw in beverage_keywords):
                return True

        # 5. 泰国来源的食品/饮料新闻（IF原产地）
        thai_sources = ["thai", "泰国", "bangkok", "曼谷"]
        if any(s in full_source for s in thai_sources):
            if "food" in full_text or "beverage" in full_text or "drink" in full_text:
                return True

        return False

    @classmethod
    def filter_articles(cls, articles: List[Dict]) -> List[Dict]:
        """
        过滤文章列表，只保留与IF品牌相关的

        Args:
            articles: 原始文章列表

        Returns:
            过滤后的文章列表
        """
        filtered = []
        for article in articles:
            if cls.is_brand_related(article):
                filtered.append(article)

        removed_count = len(articles) - len(filtered)
        if removed_count > 0:
            print(f"[BrandFilter] Removed {removed_count} unrelated articles, kept {len(filtered)} IF-brand related")

        return filtered


# ==================== 兼容性接口 ====================

class NewsFetcher:
    """
    兼容旧接口的包装类
    保持与原有代码的兼容性
    新增：缓存支持、多关键词搜索、品牌过滤
    """

    def __init__(self, use_cache: bool = True):
        self.aggregator = NewsAggregator(use_cache=use_cache)
        self.use_cache = use_cache

    def fetch_news(self, days_back: int = 30, max_time: int = 300, filter_brand: bool = True, use_cache: bool = None) -> List[Dict]:
        """
        兼容旧接口（支持超时限制、品牌过滤和缓存）

        Args:
            days_back: 获取多少天内的新闻
            max_time: 最大执行时间（秒），默认300秒
            filter_brand: 是否启用品牌过滤，默认True
            use_cache: 是否使用缓存（None表示使用初始化时的设置）

        Returns:
            统一格式的新闻列表
        """
        # 确定是否使用缓存
        should_use_cache = use_cache if use_cache is not None else self.use_cache

        articles = self.aggregator.fetch_all(
            days_back=days_back,
            deduplicate=True,
            max_time=max_time,
            use_cache=should_use_cache
        )

        # 品牌过滤：只保留与IF相关的新闻
        if filter_brand and articles:
            articles = BrandFilter.filter_articles(articles)

        return articles

    def clear_cache(self):
        """清除缓存"""
        if self.aggregator.cache:
            self.aggregator.cache.clear()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    # 直接运行测试
    print("Testing news fetcher module...")

    fetcher = NewsFetcher()
    articles = fetcher.fetch_news(days_back=30)

    print(f"\nFetched {len(articles)} articles:")
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']} ({article['source_type']})")
        print(f"   Date: {article['published_at']}")
