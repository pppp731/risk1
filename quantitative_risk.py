"""
quantitative_risk.py - 定量风险评估模块

基于信用风险模型(EL = PD × LGD × EAD)的简化版本，
为IF椰子水公司提供可量化的风险暴露值计算。
"""

import numpy as np
from risk_analyzer import RiskAnalyzer, calculate_probability
from datetime import datetime


def calculate_financial_adjustment(financial_data=None):
    """
    计算财务比率调整因子

    根据IFBH(6603.HK)的财务健康度，生成一个调整乘数（0.8–2.0），
    应用于PD和EAD以反映财务脆弱性对风险暴露的放大效应。

    PDF Module 7: 财务反常信号 → 风险乘数映射

    参数:
        financial_data: dict，来自 financial_monitor.get_full_report()
                       为 None 时返回 1.0（不调整）

    返回:
        dict: 调整因子详情
    """
    if not financial_data:
        return {
            "multiplier": 1.0,
            "level": "none",
            "factors": {},
            "summary": "无财务数据，不应用调整",
        }

    score = 0
    factors = {}
    health = financial_data.get("financial_health", {})
    stock = financial_data.get("stock_data", {})
    anomaly_signals = financial_data.get("anomaly_signals", [])

    # ===== 盈利能力因子 (权重25%) =====
    profit = health.get("profitability", {})
    net_profit_growth = profit.get("net_profit_growth_pct", 0)
    revenue_growth = profit.get("revenue_growth_pct", 0)

    if net_profit_growth < -30 and revenue_growth > 0:
        # 增收不增利（Module 7.1 经典反常信号）
        score += 25
        factors["profit_divergence"] = {
            "score": 25,
            "signal": f"营收+{revenue_growth}%但净利{net_profit_growth}%——增收不增利",
            "level": "critical",
        }
    elif net_profit_growth < -15:
        score += 15
        factors["profit_divergence"] = {"score": 15, "signal": f"净利润下降{abs(net_profit_growth)}%", "level": "high"}
    elif net_profit_growth < 0:
        score += 8
        factors["profit_divergence"] = {"score": 8, "signal": "净利润小幅下滑", "level": "medium"}
    else:
        factors["profit_divergence"] = {"score": 0, "signal": "盈利增长健康", "level": "low"}

    # ===== 毛利率因子 (权重15%) =====
    gross_margin = profit.get("gross_margin_pct", 40)
    gm_change = profit.get("gross_margin_change_pp", 0)

    if gross_margin < 30 and gm_change < -3:
        score += 15
        factors["margin_erosion"] = {
            "score": 15,
            "signal": f"毛利率{gross_margin}%（降{abs(gm_change)}pp）——定价权削弱",
            "level": "critical",
        }
    elif gross_margin < 35 and gm_change < 0:
        score += 10
        factors["margin_erosion"] = {"score": 10, "signal": f"毛利率{gross_margin}%（降{abs(gm_change)}pp）", "level": "high"}
    elif gm_change < 0:
        score += 5
        factors["margin_erosion"] = {"score": 5, "signal": "毛利率微降", "level": "medium"}
    else:
        factors["margin_erosion"] = {"score": 0, "signal": "毛利率稳定", "level": "low"}

    # ===== 费用效率因子 (权重15%) =====
    efficiency = health.get("efficiency", {})
    mkt_ratio = efficiency.get("marketing_expense_ratio_pct", 5)
    mkt_growth = efficiency.get("marketing_growth_pct", 0)

    if mkt_growth > 70:
        score += 15
        factors["expense_bloat"] = {
            "score": 15,
            "signal": f"营销费用率{mkt_ratio}%（同比+{mkt_growth}%）——获客成本失控",
            "level": "critical",
        }
    elif mkt_growth > 40:
        score += 10
        factors["expense_bloat"] = {"score": 10, "signal": f"营销费用增长{mkt_growth}%，远超营收增速", "level": "high"}
    elif mkt_ratio > 7:
        score += 5
        factors["expense_bloat"] = {"score": 5, "signal": "营销费率偏高", "level": "medium"}
    else:
        factors["expense_bloat"] = {"score": 0, "signal": "费用控制合理", "level": "low"}

    # ===== 集中度风险因子 (权重15%) =====
    conc = health.get("concentration_risk", {})
    top5 = conc.get("top5_customer_pct", 50)

    if top5 > 95:
        score += 15
        factors["concentration"] = {
            "score": 15,
            "signal": f"前5大客户{top5}%——极端集中",
            "level": "critical",
        }
    elif top5 > 80:
        score += 10
        factors["concentration"] = {"score": 10, "signal": f"前5大客户{top5}%——高度集中", "level": "high"}
    elif top5 > 60:
        score += 5
        factors["concentration"] = {"score": 5, "signal": "客户集中度偏高", "level": "medium"}
    else:
        factors["concentration"] = {"score": 0, "signal": "客户分散健康", "level": "low"}

    # ===== 估值/市场信心因子 (权重15%) =====
    valuation = financial_data.get("valuation_risk", {})
    drawdown = abs(valuation.get("drawdown_from_52w_high_pct", 0))

    if drawdown > 60:
        score += 15
        factors["market_confidence"] = {
            "score": 15,
            "signal": f"股价较高点跌{drawdown:.0f}%——市场信心崩溃",
            "level": "critical",
        }
    elif drawdown > 40:
        score += 10
        factors["market_confidence"] = {"score": 10, "signal": f"股价较高点跌{drawdown:.0f}%", "level": "high"}
    elif drawdown > 20:
        score += 5
        factors["market_confidence"] = {"score": 5, "signal": "股价回撤", "level": "medium"}
    else:
        factors["market_confidence"] = {"score": 0, "signal": "股价稳定", "level": "low"}

    # ===== 缓冲因子：现金储备 (权重-15%，可抵减) =====
    bs = health.get("balance_sheet", {})
    cash = bs.get("cash_usd_m", 0)
    cash_ratio = bs.get("cash_to_revenue_pct", 0)

    if cash > 100 and cash_ratio > 50:
        score -= 10
        factors["cash_buffer"] = {
            "score": -10,
            "signal": f"现金${cash}M（占营收{cash_ratio}%）——财务缓冲充足",
            "level": "strong",
        }
    elif cash > 50:
        score -= 5
        factors["cash_buffer"] = {"score": -5, "signal": "现金储备尚可", "level": "adequate"}
    else:
        factors["cash_buffer"] = {"score": 0, "signal": "现金储备偏低", "level": "weak"}

    # ===== 反常信号数量额外加权 =====
    anomaly_count = len(anomaly_signals)
    if anomaly_count >= 5:
        score += 10
    elif anomaly_count >= 3:
        score += 5

    # ===== 映射到调整乘数 =====
    score = max(score, 0)  # 不低于0（现金缓冲可能抵减）
    if score >= 60:
        multiplier = 1.8
        level = "critical"
        summary = f"财务状况严重恶化（评分{score}），风险乘数{multiplier}×"
    elif score >= 40:
        multiplier = 1.45
        level = "high"
        summary = f"财务风险偏高（评分{score}），风险乘数{multiplier}×"
    elif score >= 20:
        multiplier = 1.2
        level = "medium"
        summary = f"财务风险中等（评分{score}），风险乘数{multiplier}×"
    elif score >= 5:
        multiplier = 1.05
        level = "low"
        summary = f"财务基本健康（评分{score}），轻微调整"
    else:
        multiplier = 0.9  # 财务健康时可略微下调风险
        level = "strong"
        summary = f"财务稳健（评分{score}），风险折扣{multiplier}×"

    return {
        "multiplier": round(multiplier, 2),
        "total_score": score,
        "level": level,
        "factors": factors,
        "summary": summary,
    }


def calculate_EL(news_list, sentiment_scores, financial_data=None):
    """
    计算预期损失(Expected Loss)

    公式: EL = PD × LGD × EAD

    参数:
        news_list: 新闻分析结果列表，每项包含 'risks' 字段
        sentiment_scores: 情感分数列表(极性值，负数表示负面)

    返回:
        dict: 包含EL值及各组成部分的字典
    """
    if not news_list or not sentiment_scores:
        return {
            "EL": 0.0,
            "PD": 0.0,
            "LGD": 0.0,
            "EAD": 100,
            "details": "无数据"
        }

    # ========== PD (Probability of Default) 计算 ==========
    # PD = 负面新闻占比 × 平均负面强度

    # 统计负面新闻（情感极性 < -0.1 视为负面）
    negative_scores = [s for s in sentiment_scores if s < -0.1]
    total_news = len(sentiment_scores)
    negative_count = len(negative_scores)

    # 负面新闻占比
    negative_ratio = negative_count / total_news if total_news > 0 else 0

    # 平均负面强度（取绝对值，范围0-1）
    avg_negative_intensity = abs(np.mean(negative_scores)) if negative_scores else 0

    # PD 计算（上限设为0.5，避免极端值）
    raw_PD = negative_ratio * avg_negative_intensity

    # ========== 财务比率调整（PDF Module 7）==========
    fin_adj = calculate_financial_adjustment(financial_data)
    fin_multiplier = fin_adj["multiplier"]

    # PD_adj = raw_PD × fin_multiplier（财务恶化→风险概率上升）
    PD = min(raw_PD * fin_multiplier, 0.5)

    # EAD_adj = 100 × fin_multiplier（财务恶化→品牌风险暴露增大）
    # 财务健康时（multiplier < 1.0），EAD可低于100
    EAD = max(round(100 * fin_multiplier), 60)

    # ========== LGD (Loss Given Default) 计算 ==========
    # 根据风险类型关键词映射损失程度

    risk_type_weights = {
        # 法律/召回类 - 最高损失
        "法律风险": 0.8,
        "供应链风险": 0.8,  # 包含召回、质量问题

        # 财务/质量类 - 中等损失
        "财务风险": 0.5,

        # 舆情类 - 较低损失
        "声誉风险": 0.3,
        "劳工风险": 0.3,
        "环境风险": 0.3,
    }

    total_weight = 0.0
    risk_count = 0

    for news in news_list:
        risks = news.get("risks", [])
        for risk in risks:
            risk_type = risk.get("risk_type", "")
            weight = risk_type_weights.get(risk_type, 0.3)  # 默认0.3
            total_weight += weight
            risk_count += 1

    # LGD 为加权平均值，范围 0.1-0.9
    if risk_count > 0:
        LGD = min(max(total_weight / risk_count, 0.1), 0.9)
    else:
        LGD = 0.1  # 无明确风险时设为基础值

    # ========== EL 计算 ==========
    EL = PD * LGD * EAD

    return {
        "EL": float(round(EL, 3)),
        "PD": float(round(PD, 3)),
        "raw_PD": float(round(raw_PD, 3)),
        "LGD": float(round(LGD, 3)),
        "EAD": EAD,
        "financial_adjustment": fin_adj,
        "details": {
            "negative_ratio": float(round(negative_ratio, 3)),
            "avg_negative_intensity": float(round(avg_negative_intensity, 3)),
            "negative_count": negative_count,
            "total_news": total_news,
            "risk_count": risk_count,
            "risk_type_distribution": _get_risk_distribution(news_list)
        }
    }


def _get_risk_distribution(news_list):
    """
    统计风险类型分布

    参数:
        news_list: 新闻分析结果列表

    返回:
        dict: 各风险类型出现次数
    """
    distribution = {}
    for news in news_list:
        for risk in news.get("risks", []):
            risk_type = risk.get("risk_type", "未知")
            distribution[risk_type] = distribution.get(risk_type, 0) + 1
    return distribution


def calculate_simple_VaR(sentiment_scores, confidence=0.95):
    """
    计算简化版VaR (Value at Risk)

    VaR表示在给定置信水平下，可能面临的最大损失（最差负面程度）。

    参数:
        sentiment_scores: 历史情感分数列表（负数表示负面）
        confidence: 置信水平，默认0.95（95%）

    返回:
        dict: 包含VaR值及统计信息的字典
    """
    if not sentiment_scores:
        return {
            "VaR": 0.0,
            "confidence": confidence,
            "percentile": 0.0,
            "mean_sentiment": 0.0,
            "std_sentiment": 0.0,
            "sample_size": 0
        }

    scores = np.array(sentiment_scores)

    # 计算 (1-confidence) 百分位数
    # 例如：confidence=0.95，取第5百分位数（最差的情况）
    percentile_value = np.percentile(scores, (1 - confidence) * 100)

    # VaR = 百分位数的负值（正值表示风险程度）
    # 如果百分位数为正（即大部分情感正面），VaR设为0
    VaR = max(-percentile_value, 0) if percentile_value < 0 else 0

    return {
        "VaR": float(round(VaR, 3)),
        "confidence": confidence,
        "percentile": float(round(percentile_value, 3)),
        "mean_sentiment": float(round(float(np.mean(scores)), 3)),
        "std_sentiment": float(round(float(np.std(scores)), 3)),
        "sample_size": len(sentiment_scores),
        "min_sentiment": float(round(float(np.min(scores)), 3)),
        "max_sentiment": float(round(float(np.max(scores)), 3))
    }


def stress_test(news_list, sentiment_scores, financial_data=None):
    """
    压力测试 - 模拟极端负面新闻爆发场景

    情景设定：前3条负面新闻的影响程度提高50%

    参数:
        news_list: 新闻分析结果列表
        sentiment_scores: 情感分数列表

    返回:
        dict: 压力测试结果，包含EL变化百分比等信息
    """
    if not news_list or not sentiment_scores:
        return {
            "baseline_EL": 0.0,
            "stressed_EL": 0.0,
            "change_percent": 0.0,
            "stress_multiplier": 1.5,
            "affected_count": 0,
            "message": "数据不足，无法进行压力测试"
        }

    # 计算基准EL（含财务调整）
    baseline = calculate_EL(news_list, sentiment_scores, financial_data)
    baseline_EL = baseline["EL"]

    # 找出前3条负面新闻
    negative_indices = []
    for i, news in enumerate(news_list):
        polarity = news.get("sentiment", {}).get("polarity", 0)
        if polarity < -0.1:
            negative_indices.append(i)
        if len(negative_indices) >= 3:
            break

    # 如果没有负面新闻，返回基准值
    if not negative_indices:
        return {
            "baseline_EL": baseline_EL,
            "stressed_EL": baseline_EL,
            "change_percent": 0.0,
            "stress_multiplier": 1.5,
            "affected_count": 0,
            "message": "未检测到负面新闻，压力测试无影响"
        }

    # 构建压力情景下的新闻列表
    stressed_news_list = []
    for i, news in enumerate(news_list):
        stressed_news = news.copy()

        # 如果是前3条负面新闻，增强其风险影响
        if i in negative_indices:
            # 增强负面情感（使其更负面）
            if "sentiment" in stressed_news:
                original_polarity = stressed_news["sentiment"].get("polarity", 0)
                # 负面程度加深50%（更负）
                stressed_news["sentiment"]["polarity"] = original_polarity * 1.5

            # 增加风险严重程度
            if "risks" in stressed_news:
                for risk in stressed_news["risks"]:
                    original_severity = risk.get("severity", 1)
                    risk["severity"] = int(original_severity * 1.5)

        stressed_news_list.append(stressed_news)

    # 构建压力情景下的情感分数
    stressed_scores = sentiment_scores.copy()
    for idx in negative_indices:
        if idx < len(stressed_scores):
            stressed_scores[idx] = stressed_scores[idx] * 1.5

    # 计算压力情景下的EL（含财务调整）
    stressed = calculate_EL(stressed_news_list, stressed_scores, financial_data)
    stressed_EL = stressed["EL"]

    # 计算变化百分比
    if baseline_EL > 0:
        change_percent = ((stressed_EL - baseline_EL) / baseline_EL) * 100
    else:
        change_percent = 0.0 if stressed_EL == 0 else 100.0

    return {
        "baseline_EL": float(baseline_EL),
        "stressed_EL": float(stressed_EL),
        "change_percent": float(round(change_percent, 2)),
        "stress_multiplier": 1.5,
        "affected_count": len(negative_indices),
        "affected_indices": negative_indices,
        "baseline_details": {
            "PD": float(baseline["PD"]),
            "LGD": float(baseline["LGD"])
        },
        "stressed_details": {
            "PD": float(stressed["PD"]),
            "LGD": float(stressed["LGD"])
        },
        "message": f"压力情景下EL上升{change_percent:.1f}%，需关注负面舆情恶化风险"
    }


def scenario_analysis(news_list, sentiment_scores, financial_data=None):
    """
    多情景分析引擎 — 从单一EL扩展为四情景概率加权模型

    情景设定（基于IF椰子水当前风险态势）：

    ┌──────────┬────────┬────────────────────────────────┬──────────────┐
    │ 情景     │ 概率   │ 假设条件                       │ EL调整方式   │
    ├──────────┼────────┼────────────────────────────────┼──────────────┤
    │ 乐观     │  15%   │ 舆情自然平息，Q3销售恢复       │ 负面×0.5    │
    │ 基准     │  50%   │ 现状维持，缓慢恢复             │ 标准EL      │
    │ 悲观     │  25%   │ 监管介入+产品召回+海关严查     │ 负面×1.8    │
    │ 极端     │  10%   │ 品牌死亡螺旋: 大规模诉讼+下架  │ 负面×2.5    │
    └──────────┴────────┴────────────────────────────────┴──────────────┘

    参数:
        news_list: 新闻分析结果列表
        sentiment_scores: 情感分数列表
        financial_data: 财务监控数据

    返回:
        dict: 多情景分析结果
    """
    if not news_list or not sentiment_scores:
        return {"weighted_EL": 0.0, "scenarios": [], "verdict": "数据不足"}

    scenarios_config = [
        {
            "name": "乐观情景",
            "name_en": "Optimistic",
            "probability": 0.15,
            "prob_label": "15%",
            "description": "微博热度自然下降，SGS检测报告获认可，Q3销售触底反弹",
            "sentiment_factor": 0.5,   # 负面减半
            "risk_severity_factor": 0.7,
            "ecom_recovery": True,
            "color": "#00c853",
        },
        {
            "name": "基准情景",
            "name_en": "Baseline",
            "probability": 0.50,
            "prob_label": "50%",
            "description": "负面舆情持续但强度减弱，销售缓慢恢复，无新增重大风险",
            "sentiment_factor": 1.0,   # 不变
            "risk_severity_factor": 1.0,
            "ecom_recovery": False,
            "color": "#fee440",
        },
        {
            "name": "悲观情景",
            "name_en": "Pessimistic",
            "probability": 0.25,
            "prob_label": "25%",
            "description": "市场监管总局正式介入调查，启动产品召回，海关加强椰子水进口检验",
            "sentiment_factor": 1.8,   # 负面加深80%
            "risk_severity_factor": 1.5,
            "ecom_recovery": False,
            "color": "#ff6b6b",
        },
        {
            "name": "极端情景",
            "name_en": "Extreme",
            "probability": 0.10,
            "prob_label": "10%",
            "description": "大规模集体诉讼+平台全线下架+泰国工厂注册被吊销+品牌永久受损",
            "sentiment_factor": 2.5,   # 负面加深150%
            "risk_severity_factor": 2.0,
            "ecom_recovery": False,
            "color": "#ef233c",
        },
    ]

    # 基准EL（作为基准情景）
    baseline = calculate_EL(news_list, sentiment_scores, financial_data)
    baseline_el = baseline["EL"]
    baseline_pd = baseline["PD"]

    scenarios = []
    weighted_el_sum = 0
    total_prob = 0

    for cfg in scenarios_config:
        # 调整新闻列表和情感分数
        adj_scores = [s * cfg["sentiment_factor"] if s < -0.1 else s for s in sentiment_scores]

        adj_news = []
        for news in news_list:
            n = news.copy()
            if n.get("sentiment", {}).get("polarity", 0) < -0.1:
                n["sentiment"] = n.get("sentiment", {}).copy()
                n["sentiment"]["polarity"] *= cfg["sentiment_factor"]
            if "risks" in n:
                n["risks"] = []
                for risk in news.get("risks", []):
                    r = risk.copy()
                    r["severity"] = int(r.get("severity", 1) * cfg["risk_severity_factor"])
                    n["risks"].append(r)
            adj_news.append(n)

        # 计算该情景的EL
        el_result = calculate_EL(adj_news, adj_scores, financial_data)
        el_val = el_result["EL"]

        weighted_el_sum += el_val * cfg["probability"]
        total_prob += cfg["probability"]

        scenarios.append({
            "name": cfg["name"],
            "name_en": cfg["name_en"],
            "probability": cfg["probability"],
            "prob_label": cfg["prob_label"],
            "description": cfg["description"],
            "color": cfg["color"],
            "EL": float(round(el_val, 2)),
            "PD": el_result["PD"],
            "LGD": el_result["LGD"],
            "EAD": el_result["EAD"],
            "sentiment_adjustment": cfg["sentiment_factor"],
            "vs_baseline_pct": float(round(
                ((el_val - baseline_el) / baseline_el * 100) if baseline_el > 0 else 0, 1
            )),
        })

    weighted_EL = weighted_el_sum / total_prob if total_prob > 0 else baseline_el

    # 计算风险分布统计
    el_values = [s["EL"] for s in scenarios]
    best_case = min(el_values)
    worst_case = max(el_values)
    el_range = worst_case - best_case

    # 判定：加权EL在什么区间
    if weighted_EL > 50:
        verdict = "CRITICAL — 加权EL超过50，即使在乐观情景下EL仍偏高，建议立即启动全面应对"
        risk_band = "critical"
    elif weighted_EL > 25:
        verdict = "ELEVATED — 加权EL偏高，乐观与悲观情景差距大，不确定性高，需制定弹性应对方案"
        risk_band = "high"
    elif weighted_EL > 10:
        verdict = "MODERATE — 基准情景可控，但悲观情景有上行风险，建议保持监控并准备预案"
        risk_band = "medium"
    else:
        verdict = "LOW — 风险可控，维持常规监控即可"
        risk_band = "low"

    return {
        "weighted_EL": float(round(weighted_EL, 2)),
        "baseline_EL": float(round(baseline_el, 2)),
        "verdict": verdict,
        "risk_band": risk_band,
        "distribution": {
            "best_case": float(round(best_case, 2)),
            "worst_case": float(round(worst_case, 2)),
            "range": float(round(el_range, 2)),
            "range_pct_of_baseline": float(round(el_range / baseline_el * 100, 1)) if baseline_el > 0 else 0,
        },
        "scenarios": scenarios,
        "probability_weighted": {
            "upside_only": float(round((weighted_EL - best_case), 2)),
            "downside_risk": float(round((worst_case - weighted_EL), 2)),
            "asymmetry": "downside-dominated" if (worst_case - weighted_EL) > (weighted_EL - best_case) * 2 else "balanced",
        },
    }


def comprehensive_risk_report(news_list, sentiment_scores, confidence=0.95, financial_data=None):
    """
    生成综合定量风险报告

    参数:
        news_list: 新闻分析结果列表
        sentiment_scores: 情感分数列表
        confidence: VaR置信水平，默认0.95
        financial_data: 财务监控数据（来自 financial_monitor），可选

    返回:
        dict: 综合风险报告，包含EL、VaR、压力测试结果
    """
    # 计算各项指标
    el_result = calculate_EL(news_list, sentiment_scores, financial_data)
    var_result = calculate_simple_VaR(sentiment_scores, confidence)
    stress_result = stress_test(news_list, sentiment_scores, financial_data)

    # 多情景分析
    scenario_result = scenario_analysis(news_list, sentiment_scores, financial_data)

    # 风险评级
    risk_rating = _assess_risk_rating(el_result["EL"], var_result["VaR"])

    return {
        "summary": {
            "risk_rating": risk_rating,
            "overall_score": _calculate_overall_score(el_result, var_result),
            "assessment_date": str(datetime.now())
        },
        "expected_loss": el_result,
        "value_at_risk": var_result,
        "stress_test": stress_result,
        "scenario_analysis": scenario_result,
        "recommendations": _generate_recommendations(el_result, var_result, stress_result)
    }


def _assess_risk_rating(el, var):
    """
    根据EL和VaR评估风险等级
    """
    # 综合评分 (0-100)
    score = (el * 10) + (var * 50)

    if score >= 30:
        return "高风险"
    elif score >= 15:
        return "中风险"
    else:
        return "低风险"


def _calculate_overall_score(el_result, var_result):
    """
    计算综合风险评分
    """
    el_score = min(el_result["EL"] * 10, 50)  # EL贡献最高50分
    var_score = min(var_result["VaR"] * 50, 50)  # VaR贡献最高50分
    return round(el_score + var_score, 2)


def _generate_recommendations(el_result, var_result, stress_result):
    """
    生成风险应对建议
    """
    recommendations = []

    # 基于EL的建议
    if el_result["PD"] > 0.3:
        recommendations.append("负面新闻占比较高，建议加强舆情监控和公关应对")
    if el_result["LGD"] > 0.6:
        recommendations.append("检测到高损失风险类型（法律/召回类），建议启动合规审查")

    # 基于VaR的建议
    if var_result["VaR"] > 0.5:
        recommendations.append("情感波动风险较大，建议建立舆情预警机制")

    # 基于压力测试的建议
    if stress_result["change_percent"] > 50:
        recommendations.append("压力测试显示极端情景下风险显著上升，建议制定应急预案")

    if not recommendations:
        recommendations.append("当前风险可控，建议维持常规监控")

    return recommendations
