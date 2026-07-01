"""
risk_analyzer.py - 风险分析模块
核心功能：情感分析 + 风险识别 + 风险评分
"""

from baidu_nlp import SentimentAnalyzer
from config import RISK_KEYWORDS, RISK_THRESHOLDS, BAIDU_API_KEY, BAIDU_SECRET_KEY
import re
from datetime import datetime, timedelta


class RiskAnalyzer:
    """风险分析器类 - 分析单条新闻的风险"""

    def __init__(self):
        """初始化分析器"""
        self.risk_keywords = RISK_KEYWORDS
        # 初始化智能情感分析器（自动识别中英文）
        self.sentiment_analyzer = SentimentAnalyzer(
            baidu_api_key=BAIDU_API_KEY if BAIDU_API_KEY != "your_baidu_api_key_here" else None,
            baidu_secret_key=BAIDU_SECRET_KEY if BAIDU_SECRET_KEY != "your_baidu_secret_key_here" else None
        )

    def analyze_sentiment(self, text):
        """
        情感分析 - 判断文本是正面还是负面
        自动检测语言，中文使用百度NLP，英文使用TextBlob

        参数:
            text: 要分析的文本

        返回:
            dict: 包含极性(polarity)和主观性(subjectivity)的字典
                - polarity: -1(负面) 到 1(正面)
                - subjectivity: 0(客观) 到 1(主观)
                - sentiment_label: 正面/负面/中性
                - confidence: 置信度
                - source: 分析来源 (baidu_nlp/textblob)
        """
        if not text:
            return {
                "polarity": 0,
                "subjectivity": 0,
                "sentiment_label": "中性",
                "confidence": 0,
                "source": "none"
            }

        # 使用智能情感分析器
        result = self.sentiment_analyzer.analyze(text)
        return result

    def identify_risks(self, text):
        """
        风险识别 - 识别文本中包含的风险类型

        参数:
            text: 要分析的文本

        返回:
            list: 风险类型列表，每项包含风险类型、关键词、证据
        """
        if not text:
            return []

        text_lower = text.lower()
        identified_risks = []

        # 遍历所有风险类型和关键词
        for risk_type, keywords in self.risk_keywords.items():
            matched_keywords = []
            evidence = []

            for keyword in keywords:
                # 使用正则表达式匹配关键词（忽略大小写）
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    matched_keywords.append(keyword)
                    # 提取关键词周围的上下文作为证据
                    evidence.append(self._extract_context(text, keyword))

            # 如果匹配到关键词，记录该风险
            if matched_keywords:
                identified_risks.append({
                    "risk_type": risk_type,
                    "keywords_found": matched_keywords,
                    "evidence": list(set(evidence))[:2],  # 最多2条证据
                    "severity": len(matched_keywords)  # 匹配越多，严重程度越高
                })

        return identified_risks

    def _extract_context(self, text, keyword, window=50):
        """
        提取关键词周围的上下文

        参数:
            text: 原文本
            keyword: 关键词
            window: 前后提取的字符数

        返回:
            str: 包含关键词的上下文
        """
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # 找到关键词位置
        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return ""

        # 提取上下文
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)

        context = text[start:end]

        # 添加省略号表示截取
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def calculate_risk_score(self, sentiment, risks):
        """
        计算风险评分

        评分规则:
        - 基础分: 50分
        - 负面情感加分 (0-30分)
        - 风险类型加分 (每个风险类型10-20分)
        - 风险严重程度加分 (0-20分)

        参数:
            sentiment: 情感分析结果
            risks: 识别的风险列表

        返回:
            dict: 包含总评分和评分详情
        """
        score_details = {
            "base_score": 50,
            "sentiment_score": 0,
            "risk_type_score": 0,
            "severity_score": 0,
            "total_score": 50
        }

        # 负面情感增加风险分数
        polarity = sentiment.get("polarity", 0)
        if polarity < -0.1:
            # 越负面分数越高
            sentiment_score = abs(polarity) * 30
            score_details["sentiment_score"] = round(sentiment_score, 1)

        # 风险类型数量增加分数
        if risks:
            risk_type_score = len(risks) * 10
            score_details["risk_type_score"] = risk_type_score

            # 风险严重程度
            total_severity = sum(r.get("severity", 0) for r in risks)
            severity_score = min(total_severity * 3, 20)  # 最高20分
            score_details["severity_score"] = severity_score

        # 计算总分
        total = sum([
            score_details["base_score"],
            score_details["sentiment_score"],
            score_details["risk_type_score"],
            score_details["severity_score"]
        ])
        score_details["total_score"] = min(round(total), 100)

        # 确定风险等级
        score_details["risk_level"] = self._get_risk_level(score_details["total_score"])

        return score_details

    def _get_risk_level(self, score):
        """
        根据分数确定风险等级

        参数:
            score: 风险分数 (0-100)

        返回:
            str: 风险等级
        """
        if score >= RISK_THRESHOLDS["high"]:
            return "严重风险"
        elif score >= RISK_THRESHOLDS["medium"]:
            return "高风险"
        elif score >= RISK_THRESHOLDS["low"]:
            return "中风险"
        else:
            return "低风险"

    def analyze_article(self, article):
        """
        分析单条新闻 - 主入口函数

        参数:
            article: 新闻字典，包含title, description等字段

        返回:
            dict: 完整的分析结果
        """
        # 合并标题和描述进行分析
        full_text = f"{article.get('title', '')} {article.get('description', '')}"

        # 1. 情感分析
        sentiment = self.analyze_sentiment(full_text)

        # 2. 风险识别
        risks = self.identify_risks(full_text)

        # 3. 风险评分
        score = self.calculate_risk_score(sentiment, risks)

        # 计算风险概率和风险矩阵等级
        probability = calculate_probability(article)
        # 将总分(0-100)归一化为影响程度(0-1)
        impact = score["total_score"] / 100.0
        risk_level = risk_matrix(impact, probability)
        risk_score = impact * probability  # 风险综合得分

        return {
            "article": article,
            "sentiment": sentiment,
            "risks": risks,
            "score": score,
            "has_risk": len(risks) > 0 or sentiment.get("polarity", 0) < -0.1,
            "probability": round(probability, 3),
            "risk_level": risk_level,
            "risk_score": round(risk_score, 3)
        }


class PortfolioRiskAnalyzer:
    """组合风险分析器 - 分析多条新闻的综合风险"""

    def __init__(self):
        self.analyzer = RiskAnalyzer()

    def analyze_portfolio(self, articles):
        """
        分析一组新闻，生成综合报告

        参数:
            articles: 新闻列表

        返回:
            dict: 综合分析报告
        """
        if not articles:
            return {"error": "没有可分析的新闻"}

        # 分析每条新闻
        analyzed_articles = []
        all_risk_types = {}
        total_score = 0
        risk_count = 0
        sentiment_distribution = {"正面": 0, "负面": 0, "中性": 0}

        for article in articles:
            result = self.analyzer.analyze_article(article)
            analyzed_articles.append(result)

            # 统计情感分布
            sentiment_label = result["sentiment"].get("sentiment_label", "中性")
            sentiment_distribution[sentiment_label] += 1

            # 统计风险类型
            for risk in result["risks"]:
                risk_type = risk["risk_type"]
                if risk_type not in all_risk_types:
                    all_risk_types[risk_type] = {"count": 0, "articles": []}
                all_risk_types[risk_type]["count"] += 1
                all_risk_types[risk_type]["articles"].append(article.get("title", ""))

            # 累计风险分数
            if result["has_risk"]:
                total_score += result["score"]["total_score"]
                risk_count += 1

        # 计算平均风险分数
        avg_score = total_score / risk_count if risk_count > 0 else 0

        # 生成预警建议
        warnings = self._generate_warnings(all_risk_types, avg_score, sentiment_distribution)

        return {
            "total_articles": len(articles),
            "risky_articles": risk_count,
            "average_risk_score": round(avg_score, 1),
            "overall_risk_level": self._get_overall_risk_level(avg_score),
            "sentiment_distribution": sentiment_distribution,
            "risk_type_summary": all_risk_types,
            "analyzed_articles": analyzed_articles,
            "warnings": warnings
        }

    def _generate_warnings(self, risk_types, avg_score, sentiment_dist):
        """
        生成风险预警建议

        参数:
            risk_types: 风险类型统计
            avg_score: 平均风险分数
            sentiment_dist: 情感分布

        返回:
            list: 预警建议列表
        """
        warnings = []

        # 根据平均分数预警
        if avg_score >= 80:
            warnings.append({
                "level": "严重",
                "message": "检测到严重风险信号，建议立即采取应对措施！"
            })
        elif avg_score >= 60:
            warnings.append({
                "level": "高",
                "message": "存在较高风险，需要密切关注并准备应对预案。"
            })
        elif avg_score >= 40:
            warnings.append({
                "level": "中",
                "message": "存在一定风险，建议定期监控。"
            })

        # 根据负面新闻比例预警
        total = sum(sentiment_dist.values())
        if total > 0:
            negative_ratio = sentiment_dist["负面"] / total
            if negative_ratio > 0.5:
                warnings.append({
                    "level": "高",
                    "message": f"负面新闻占比高达{negative_ratio*100:.1f}%，需特别关注舆情变化。"
                })

        # 根据风险类型预警
        for risk_type, data in risk_types.items():
            if data["count"] >= 3:
                warnings.append({
                    "level": "中",
                    "message": f"检测到多次{risk_type}相关报道（{data['count']}次），建议专项调查。"
                })

        if not warnings:
            warnings.append({
                "level": "低",
                "message": "整体风险可控，继续保持监控即可。"
            })

        return warnings

    def _get_overall_risk_level(self, score):
        """获取整体风险等级"""
        if score >= 80:
            return "严重风险"
        elif score >= 60:
            return "高风险"
        elif score >= 40:
            return "中风险"
        elif score > 0:
            return "低风险"
        else:
            return "无风险"


def calculate_probability(article):
    """
    计算单条新闻的风险发生概率

    评估维度:
    - 新闻来源权威性: Reuters/Bloomberg +0.2, 主流商业媒体 +0.1, 其他 +0.05
    - 关键词强度: 高风险词(recall/诉讼/调查等) +0.3, 中风险词(质疑/下降等) +0.15
    - 新闻时效性: 3天内 +0.1, 一周内 +0.05, 超过一周 0
    - 基础概率 0.3, 上限 0.95

    参数:
        article: 新闻字典，包含source, title, description, published_at等字段

    返回:
        float: 风险发生概率 (0-1)
    """
    base_probability = 0.3
    source_weight = 0.0
    keyword_weight = 0.0
    timeliness_weight = 0.0

    # 1. 评估新闻来源权威性
    source = article.get("source", "").lower()
    high_credibility = ["reuters", "bloomberg", "financial times", "ft.com",
                        "wall street journal", "wsj", "cnbc", "marketwatch",
                        "路透社", "彭博", "华尔街日报", "金融时报"]
    medium_credibility = ["seeking alpha", "business insider", "forbes",
                          "yahoo finance", "google news", "food dive",
                          "supply chain dive", "grocery dive", "bevnet",
                          "财新", "第一财经", "21世纪经济报道"]

    if any(s in source for s in high_credibility):
        source_weight = 0.2
    elif any(s in source for s in medium_credibility):
        source_weight = 0.1
    else:
        source_weight = 0.05

    # 2. 评估关键词强度
    full_text = f"{article.get('title', '')} {article.get('description', '')}".lower()

    # 高风险关键词 - 直接表明风险事件已发生
    high_risk_keywords = [
        "recall", "lawsuit", "litigation", "investigation", "strike",
        "bankruptcy", "fraud", "scandal", "contamination", "violation",
        "召回", "诉讼", "调查", "罢工", "破产", "欺诈", "丑闻",
        "污染", "违规", "停产", "关闭", "下架"
    ]

    # 中风险关键词 - 潜在风险信号
    medium_risk_keywords = [
        "question", "doubt", "decline", "drop", "fall", "concern",
        "risk", "warning", "challenge", "pressure", "dispute",
        "质疑", "下降", "下跌", "下滑", "担忧", "关注", "风险",
        "警告", "挑战", "压力", "纠纷", "紧张", "不确定"
    ]

    has_high_risk = any(kw in full_text for kw in high_risk_keywords)
    has_medium_risk = any(kw in full_text for kw in medium_risk_keywords)

    if has_high_risk:
        keyword_weight = 0.3
    elif has_medium_risk:
        keyword_weight = 0.15

    # 3. 评估新闻时效性
    published_at = article.get("published_at") or article.get("publishedAt") or article.get("date")
    if published_at:
        try:
            if isinstance(published_at, str):
                # 尝试解析多种日期格式
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                           "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        pub_date = datetime.strptime(published_at[:19], fmt[:19])
                        break
                    except ValueError:
                        continue
                else:
                    pub_date = None
            else:
                pub_date = published_at

            if pub_date:
                days_ago = (datetime.now() - pub_date).days
                if days_ago <= 3:
                    timeliness_weight = 0.1
                elif days_ago <= 7:
                    timeliness_weight = 0.05
        except (ValueError, TypeError):
            pass

    # 计算总概率
    probability = base_probability + source_weight + keyword_weight + timeliness_weight
    return min(probability, 0.95)


def risk_matrix(impact, probability):
    """
    风险矩阵评估 - 根据影响程度和概率确定风险等级

    评估标准:
    - 高风险: impact > 0.5 且 probability > 0.6
    - 中风险: (impact > 0.3 且 probability > 0.4) 或 (impact * probability > 0.2)
    - 低风险: 其余情况

    参数:
        impact: 影响程度 (0-1)，可从风险评分归一化得到
        probability: 发生概率 (0-1)

    返回:
        str: 风险等级 ("高"/"中"/"低")
    """
    risk_score = impact * probability

    if impact > 0.5 and probability > 0.6:
        return "高"
    elif (impact > 0.3 and probability > 0.4) or risk_score > 0.2:
        return "中"
    else:
        return "低"
