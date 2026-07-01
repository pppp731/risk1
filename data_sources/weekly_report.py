"""
weekly_report.py - 自动周报生成器

聚合所有监控模块数据，生成结构化周报：
1. 执行摘要（3-5句话）
2. 关键风险指标仪表盘（红/黄/绿）
3. 本周TOP3风险
4. 环比上周变化（趋势对比）
5. 建议行动项
6. 下周关注事项

设计原则：
- 不用LLM也能生成有价值的结构化报告
- 所有文字来自预设模板 + 指标插值
- 自动存储快照用于环比对比
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class WeeklyReportGenerator:
    """周报生成器"""

    SNAPSHOT_FILE = "data/weekly_snapshot.json"

    def __init__(self):
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        if not os.path.exists("data"):
            os.makedirs("data")

    def generate(self) -> Dict:
        """
        生成完整周报

        聚合来源：
        - risk_analysis (新闻舆情)
        - quantitative (EL/VaR/情景)
        - ecommerce (电商)
        - enterprise (企业风险)
        - financial (IFBH财务)
        - policy (政策红线)
        - bottleneck (卡脖子)
        - response_plan (应对方案)
        """
        print("[WeeklyReport] Aggregating all modules...")

        # 1. 收集所有数据
        snapshot = self._collect_snapshot()

        # 2. 加载上周快照用于环比
        prev = self._load_previous_snapshot()

        # 3. 保存当前快照
        self._save_snapshot(snapshot)

        # 4. 生成报告
        report = {
            "meta": {
                "report_type": "风险哨兵智能体 — 周报",
                "period": self._get_period_label(),
                "generated_at": datetime.now().isoformat(),
                "version": "2.0",
                "has_previous_data": prev is not None,
            },
            "executive_summary": self._gen_executive_summary(snapshot, prev),
            "traffic_light_dashboard": self._gen_traffic_light(snapshot),
            "top3_risks": self._gen_top3_risks(snapshot),
            "week_over_week": self._gen_wow_comparison(snapshot, prev),
            "recommended_actions": self._gen_actions(snapshot),
            "next_week_watch": self._gen_watch_items(snapshot),
        }

        print("[WeeklyReport] Done!")
        return report

    def _get_period_label(self) -> str:
        now = datetime.now()
        monday = now - timedelta(days=now.weekday())
        sunday = monday + timedelta(days=6)
        return f"{monday.strftime('%m/%d')} - {sunday.strftime('%m/%d')}"

    def _collect_snapshot(self) -> Dict:
        """收集所有监控模块的当前快照"""
        snap = {"timestamp": datetime.now().isoformat()}

        # --- 新闻舆情 ---
        try:
            from risk_analyzer import PortfolioRiskAnalyzer
            from news_fetcher import NewsFetcher
            articles = NewsFetcher(use_cache=True).fetch_news(days_back=7, max_time=60, filter_brand=True)
            risk_report = PortfolioRiskAnalyzer().analyze_portfolio(articles)
            snap["news"] = {
                "total": risk_report.get("total_articles", 0),
                "risky": risk_report.get("risky_articles", 0),
                "avg_score": risk_report.get("average_risk_score", 0),
                "level": risk_report.get("overall_risk_level", "未知"),
                "sentiment": risk_report.get("sentiment_distribution", {}),
            }
        except Exception as e:
            snap["news"] = {"error": str(e), "total": 0}

        # --- 定量风险 ---
        try:
            from quantitative_risk import calculate_EL, calculate_simple_VaR, scenario_analysis
            scores = []
            analyzed = risk_report.get("analyzed_articles", [])
            for item in analyzed:
                scores.append(item.get("sentiment", {}).get("polarity", 0))
            depth = [r for r in analyzed if r.get("risk_level") in ("高","中")] or analyzed

            fin_data = None
            try:
                from data_sources.financial_monitor import FinancialMonitor
                fin_data = FinancialMonitor().get_full_report()
            except:
                pass

            el = calculate_EL(depth, scores, fin_data) if scores else {"EL": 0, "PD": 0}
            var = calculate_simple_VaR(scores) if scores else {"VaR": 0}
            sc = scenario_analysis(depth, scores, fin_data) if scores else None

            snap["quant"] = {
                "EL": el.get("EL", 0),
                "PD": el.get("PD", 0),
                "VaR": var.get("VaR", 0),
                "weighted_EL": sc.get("weighted_EL") if sc else 0,
                "risk_band": sc.get("risk_band") if sc else "unknown",
                "fin_multiplier": el.get("financial_adjustment", {}).get("multiplier", 1.0),
            }
        except Exception as e:
            snap["quant"] = {"error": str(e)}

        # --- 电商 ---
        try:
            from data_sources import ecommerce_monitor
            ecom = ecommerce_monitor.get_product_overview()
            tmall = ecom.get("platforms", {}).get("tmall", {})
            alerts = ecom.get("alerts", [])
            snap["ecom"] = {
                "avg_rating": tmall.get("avg_rating", 0),
                "sales_change": tmall.get("sales_change_pct", 0),
                "neg_ratio": tmall.get("negative_review_ratio", 0),
                "alert_count": len(alerts),
            }
        except Exception as e:
            snap["ecom"] = {"error": str(e)}

        # --- 企业风险 ---
        try:
            from data_sources import enterprise_monitor
            ent = enterprise_monitor.get_full_report()
            snap["enterprise"] = {
                "risk_score": ent.get("risk_score", {}).get("total_score", 0),
                "alert_count": len(ent.get("alerts", [])),
            }
        except Exception as e:
            snap["enterprise"] = {"error": str(e)}

        # --- 财务 ---
        try:
            if fin_data is None:
                from data_sources.financial_monitor import FinancialMonitor
                fin_data = FinancialMonitor().get_full_report()
            snap["financial"] = {
                "price": fin_data.get("stock_data", {}).get("current_price_hkd", 0),
                "fin_risk_score": fin_data.get("overall_financial_risk_score", {}).get("total_score", 0),
                "anomaly_count": len(fin_data.get("anomaly_signals", [])),
            }
        except Exception as e:
            snap["financial"] = {"error": str(e)}

        # --- 政策 ---
        try:
            from data_sources.policy_monitor import PolicyMonitor
            pol = PolicyMonitor().get_full_report()
            gaps = pol.get("compliance_gaps", [])
            snap["policy"] = {
                "risk_score": pol.get("policy_risk_score", {}).get("total_score", 0),
                "critical_gaps": sum(1 for g in gaps if g["severity"] == "critical"),
                "imminent_deadlines": sum(1 for d in pol.get("upcoming_deadlines", []) if d["days_remaining"] < 30),
            }
        except Exception as e:
            snap["policy"] = {"error": str(e)}

        return snap

    def _load_previous_snapshot(self) -> Optional[Dict]:
        if os.path.exists(self.SNAPSHOT_FILE):
            try:
                with open(self.SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None

    def _save_snapshot(self, snap: Dict):
        try:
            with open(self.SNAPSHOT_FILE, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
        except:
            pass

    # ====== 报告生成方法 ======

    def _gen_executive_summary(self, snap: Dict, prev: Optional[Dict]) -> str:
        """生成执行摘要"""
        parts = []

        news = snap.get("news", {})
        quant = snap.get("quant", {})
        financial = snap.get("financial", {})
        policy = snap.get("policy", {})

        # 总体态势
        avg_score = news.get("avg_score", 0)
        if avg_score >= 80:
            parts.append("本周风险态势严峻")
        elif avg_score >= 60:
            parts.append("本周风险处于较高水平")
        elif avg_score >= 40:
            parts.append("本周风险处于中等水平")
        else:
            parts.append("本周风险态势相对可控")

        # 核心指标
        el = quant.get("EL", 0)
        parts.append(f"，预期声誉损失EL={el:.1f}（{'恶化' if el > 15 else '可控'}）")

        # 环比变化
        if prev:
            prev_score = prev.get("news", {}).get("avg_score", 0)
            delta = avg_score - prev_score
            if abs(delta) > 5:
                parts.append(f"，较上周{'上升' if delta > 0 else '下降'}{abs(delta):.0f}分")

        # 重点风险
        fin_score = financial.get("fin_risk_score", 0)
        policy_score = policy.get("risk_score", 0)
        high_dims = []
        if fin_score >= 70:
            high_dims.append(f"财务风险（{fin_score}/100）")
        if policy_score >= 70:
            high_dims.append(f"政策合规（{policy_score}/100）")
        if high_dims:
            parts.append(f"。重点关注维度：{'、'.join(high_dims)}")

        parts.append("。")

        return "".join(parts)

    def _gen_traffic_light(self, snap: Dict) -> Dict:
        """生成七个模块的红绿灯仪表盘"""
        def light(score, thresholds=(30, 60)):
            if score >= thresholds[1]:
                return "red"
            elif score >= thresholds[0]:
                return "yellow"
            return "green"

        return {
            "新闻舆情": {
                "signal": light(snap.get("news", {}).get("avg_score", 0), (40, 60)),
                "value": snap.get("news", {}).get("avg_score", 0),
                "label": snap.get("news", {}).get("level", "—"),
            },
            "定量风险": {
                "signal": light(snap.get("quant", {}).get("EL", 0), (8, 15)),
                "value": round(snap.get("quant", {}).get("EL", 0), 1),
                "label": f"EL={snap.get('quant',{}).get('EL',0):.1f}",
            },
            "电商监控": {
                "signal": light(
                    abs(snap.get("ecom", {}).get("sales_change", 0)), (5, 10)
                ) if snap.get("ecom", {}).get("sales_change", 0) < 0 else "green",
                "value": snap.get("ecom", {}).get("avg_rating", 0),
                "label": f"评分{snap.get('ecom',{}).get('avg_rating',0):.1f}",
            },
            "企业风险": {
                "signal": light(snap.get("enterprise", {}).get("risk_score", 50), (40, 60)),
                "value": snap.get("enterprise", {}).get("risk_score", 0),
                "label": f"风险分{snap.get('enterprise',{}).get('risk_score',0)}",
            },
            "财务健康": {
                "signal": light(snap.get("financial", {}).get("fin_risk_score", 50), (40, 70)),
                "value": snap.get("financial", {}).get("fin_risk_score", 0),
                "label": f"{snap.get('financial',{}).get('anomaly_count',0)}个反常信号" if snap.get("financial", {}).get("anomaly_count", 0) > 0 else "健康",
            },
            "政策红线": {
                "signal": light(snap.get("policy", {}).get("risk_score", 50), (40, 70)),
                "value": snap.get("policy", {}).get("risk_score", 0),
                "label": f"{snap.get('policy',{}).get('critical_gaps',0)}个严重缺口",
            },
            "卡脖子风险": {
                "signal": "red",
                "value": 81,
                "label": "原料+采购+人才",
            },
        }

    def _gen_top3_risks(self, snap: Dict) -> List[Dict]:
        """生成本周TOP3风险"""
        risks = []

        # 从各模块收集高严重度风险
        financial = snap.get("financial", {})
        if financial.get("anomaly_count", 0) >= 4:
            risks.append({
                "rank": 1,
                "title": "IFBH财务健康持续恶化",
                "severity": "critical",
                "detail": f"检测到{financial.get('anomaly_count',0)}个财务反常信号，股价较高点跌超70%，增收不增利的商业模式瑕疵日益显著。",
                "module": "财务监控",
            })

        policy = snap.get("policy", {})
        if policy.get("imminent_deadlines", 0) > 0:
            risks.append({
                "rank": len(risks) + 1,
                "title": f"政策红线逼近：{policy.get('imminent_deadlines',0)}项法规即将/已生效",
                "severity": "critical" if policy.get("critical_gaps", 0) >= 2 else "high",
                "detail": f"海关280号令要求境外企业注册已逾期。{policy.get('critical_gaps',0)}个严重合规缺口须在短期内解决。",
                "module": "政策监控",
            })

        quant = snap.get("quant", {})
        scenario = snap.get("quant", {})
        if scenario.get("weighted_EL", 0) > 25:
            risks.append({
                "rank": len(risks) + 1,
                "title": f"多情景加权EL偏高（{scenario.get('weighted_EL',0):.1f}）",
                "severity": "high",
                "detail": f"乐观与悲观情景EL差距大，不确定性高。下行风险显著大于上行空间。",
                "module": "定量风险",
            })

        # 至少返回3条
        if len(risks) < 3:
            news = snap.get("news", {})
            if news.get("avg_score", 0) > 40:
                risks.append({
                    "rank": len(risks) + 1,
                    "title": f"负面舆情占比偏高（评分{news.get('avg_score',0):.0f}）",
                    "severity": "medium",
                    "detail": f"本周{news.get('total',0)}条新闻中{news.get('risky',0)}条存在风险信号，建议加强舆情监控。",
                    "module": "新闻舆情",
                })

        while len(risks) < 3:
            risks.append({
                "rank": len(risks) + 1,
                "title": "供应链瓶颈风险持续存在",
                "severity": "medium",
                "detail": "泰国Nam Hom香水椰100%依赖 + General Beverage单一采购通道，任何一环中断都可能导致供应危机。",
                "module": "卡脖子分析",
            })

        return risks[:5]

    def _gen_wow_comparison(self, snap: Dict, prev: Optional[Dict]) -> Optional[Dict]:
        """环比上周变化"""
        if not prev:
            return {"available": False, "message": "首次生成周报，无历史数据可对比"}

        def delta_str(key, subkey=None):
            try:
                curr = snap.get(key, {}).get(subkey, 0) if subkey else snap.get(key, 0)
                prev_v = prev.get(key, {}).get(subkey, 0) if subkey else prev.get(key, 0)
                if isinstance(curr, (int, float)) and isinstance(prev_v, (int, float)) and prev_v != 0:
                    d = curr - prev_v
                    pct = (d / abs(prev_v)) * 100
                    return {"delta": round(d, 1), "delta_pct": round(pct, 1), "direction": "up" if d > 0 else "down" if d < 0 else "flat"}
            except:
                pass
            return None

        return {
            "available": True,
            "changes": {
                "风险评分": delta_str("news", "avg_score"),
                "预期损失(EL)": delta_str("quant", "EL"),
                "IFBH股价": delta_str("financial", "price"),
                "电商评分": delta_str("ecom", "avg_rating"),
                "企业风险分": delta_str("enterprise", "risk_score"),
                "政策风险分": delta_str("policy", "risk_score"),
            },
        }

    def _gen_actions(self, snap: Dict) -> List[str]:
        """生成建议行动项"""
        actions = []

        policy = snap.get("policy", {})
        if policy.get("imminent_deadlines", 0) > 0:
            actions.append("立即处理已逾期的海关280号令境外企业注册（最紧急）")
        if policy.get("critical_gaps", 0) >= 2:
            actions.append("启动标签合规审查，确保2027年3月前完成GB 7718/GB 28050标签换版")

        financial = snap.get("financial", {})
        if financial.get("fin_risk_score", 0) >= 70:
            actions.append("建议董事会关注财务反常信号，评估是否需要调整2026年盈利指引")

        ecom = snap.get("ecom", {})
        if ecom.get("sales_change", 0) < -10:
            actions.append("天猫销量持续下滑，建议评估是否需要加大促销力度或推出新品刺激需求")

        quant = snap.get("quant", {})
        if quant.get("EL", 0) > 15:
            actions.append("EL处于中高风险区间，建议增购产品召回险并建立风险准备金")

        if len(actions) < 2:
            actions.append("本周风险态势相对可控，维持常规监控频率即可")
        actions.append("下周一召开风险管理周例会，重点审议合规整改时间表")

        return actions

    def _gen_watch_items(self, snap: Dict) -> List[str]:
        """生成下周关注事项"""
        items = [
            "关注海关总署280号令实施后的首批执法案例，评估对IF进口清关的实际影响",
            "持续监测微博#IF椰子水#话题的情感走势，关注是否有新的负面事件触发二次舆情",
            "关注泰国南部进入雨季后对椰子产量的实际影响，评估是否需要提前锁定Q3采购价格",
        ]

        quant = snap.get("quant", {})
        if quant.get("risk_band") in ("critical", "high"):
            items.append("加权EL处于高风险区间，建议每日更新情景分析，密切跟踪悲观/极端情景的触发条件")

        financial = snap.get("financial", {})
        if financial.get("fin_risk_score", 0) >= 70:
            items.append("IFBH股价若继续下行至HK$10以下，建议评估是否触发股权质押风险（如存在）")

        return items


# 全局实例
weekly_report_generator = WeeklyReportGenerator()


if __name__ == "__main__":
    gen = WeeklyReportGenerator()
    report = gen.generate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
