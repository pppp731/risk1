"""
app.py - 主程序入口
Flask Web应用，提供网页界面和API接口

智能体编排工作流：
1. 快速初筛（情感分析 + 风险矩阵）
2. 深度分析（定量风险评估 EL/VaR）
3. 动态预警 + 结构化报告生成
"""

from flask import Flask, render_template, jsonify, request
from news_fetcher import NewsFetcher
from mcp_news_fetcher import MCPNewsFetcher
from risk_analyzer import PortfolioRiskAnalyzer, RiskAnalyzer, risk_matrix
from quantitative_risk import calculate_EL, calculate_simple_VaR, stress_test, scenario_analysis
from history_manager import history_manager
from datetime import datetime
import re
import webbrowser
import threading
import time
from data_sources import ecommerce_monitor, enterprise_monitor, financial_monitor, policy_monitor, RegulatoryAlertGenerator, weekly_report_generator
from risk_response import response_engine

# 创建Flask应用实例
app = Flask(__name__)

# ============ 动态预警配置 ============
ALERT_KEYWORDS = [
    "recall", "lawsuit", "litigation", "investigation", "regulatory",
    "fine", "penalty", "violation", "sanction", "crisis",
    "召回", "诉讼", "调查", "监管", "罚款", "违规", "处罚", "危机"
]

# 存储实时预警
active_alerts = []


def check_and_trigger_alert(article, sentiment_result):
    """
    检查新闻是否需要触发实时预警
    条件：负面情感分 > 0.6 且包含预警关键词
    """
    polarity = abs(sentiment_result.get("polarity", 0))
    full_text = f"{article.get('title', '')} {article.get('description', '')}".lower()

    # 检查是否包含预警关键词
    has_alert_keyword = any(kw.lower() in full_text for kw in ALERT_KEYWORDS)

    # 负面情感 > 0.6 且包含预警关键词
    if polarity > 0.6 and has_alert_keyword:
        alert = {
            "id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().isoformat(),
            "title": article.get("title", "未知标题"),
            "source": article.get("source", "未知来源"),
            "sentiment_polarity": round(polarity, 3),
            "matched_keywords": [kw for kw in ALERT_KEYWORDS if kw.lower() in full_text],
            "severity": "高" if polarity > 0.8 else "中"
        }

        # 添加到活跃预警列表（最多保留20条）
        active_alerts.insert(0, alert)
        if len(active_alerts) > 20:
            active_alerts.pop()

        # 保存到历史记录
        history_manager.add_alert_record(alert)

        # 控制台输出预警
        print(f"\n{'='*60}")
        print(f"[ALERT] Real-time Risk Alert [{alert['severity']}]")
        print(f"Time: {alert['timestamp']}")
        print(f"Title: {alert['title']}")
        print(f"Source: {alert['source']}")
        print(f"Negative Polarity: {alert['sentiment_polarity']}")
        print(f"Matched Keywords: {', '.join(alert['matched_keywords'])}")
        print(f"{'='*60}\n")

        return alert
    return None


def workflow_analyze(articles):
    """
    智能体编排工作流：初筛 → 深度分析 → 报告生成
    """
    print("\n[Workflow] Starting agent orchestration analysis...")

    # ========== Step 1: Quick Screening ==========
    print("[Workflow] Step 1/3: Quick screening (sentiment + risk matrix)")
    analyzer = RiskAnalyzer()
    preliminary_results = []
    high_risk_articles = []
    medium_risk_articles = []

    for article in articles:
        # 快速分析单条新闻
        result = analyzer.analyze_article(article)

        # 实时预警检查
        alert = check_and_trigger_alert(article, result["sentiment"])
        if alert:
            result["alert_triggered"] = True
            result["alert_id"] = alert["id"]

        preliminary_results.append(result)

        # 按风险等级分类
        risk_level = result.get("risk_level", "低")
        if risk_level == "高":
            high_risk_articles.append(result)
        elif risk_level == "中":
            medium_risk_articles.append(result)

    # 统计风险分布
    risk_distribution = {
        "高": len(high_risk_articles),
        "中": len(medium_risk_articles),
        "低": len(preliminary_results) - len(high_risk_articles) - len(medium_risk_articles)
    }

    print(f"[Workflow] Screening complete: {len(high_risk_articles)} high risk, {len(medium_risk_articles)} medium risk, {risk_distribution['低']} low risk")

    # ========== 第二步：深度分析（针对中高风险） ==========
    quantitative_data = None
    depth_analysis_triggered = False

    if high_risk_articles or medium_risk_articles:
        depth_analysis_triggered = True
        print("[Workflow] Step 2/3: Triggering deep quantitative analysis (EL/VaR)")

        # 收集需要深度分析的文章
        depth_articles = high_risk_articles + medium_risk_articles

        # 计算定量风险指标
        sentiment_scores = [r["sentiment"]["polarity"] for r in preliminary_results]

        el_result = calculate_EL(depth_articles, sentiment_scores)
        var_result = calculate_simple_VaR(sentiment_scores, confidence=0.95)
        stress_result = stress_test(depth_articles, sentiment_scores)

        quantitative_data = {
            "EL": el_result,
            "VaR": var_result,
            "stress_test": stress_result,
            "analysis_scope": {
                "depth_analyzed": len(depth_articles),
                "high_risk_count": len(high_risk_articles),
                "medium_risk_count": len(medium_risk_articles)
            }
        }

        print(f"[Workflow] Quantitative analysis complete: EL={el_result['EL']:.2f}, VaR={var_result['VaR']:.2f}")
    else:
        print("[Workflow] Step 2/3: Risk level is low, skipping deep analysis")

    # ========== Step 3: Generate Structured Report ==========
    print("[Workflow] Step 3/3: Generating structured report")

    # 使用PortfolioRiskAnalyzer生成综合报告
    portfolio_analyzer = PortfolioRiskAnalyzer()
    base_report = portfolio_analyzer.analyze_portfolio(articles)

    # 整合工作流结果
    final_report = {
        **base_report,
        "workflow_info": {
            "version": "2.0",
            "workflow_type": "智能体编排（初筛→深度分析→动态预警）",
            "analysis_timestamp": datetime.now().isoformat(),
            "depth_analysis_triggered": depth_analysis_triggered
        },
        "risk_matrix_summary": risk_distribution,
        "quantitative_analysis": quantitative_data,
        "active_alerts": active_alerts[:5],  # 最近5条预警
        "alerts_count": len(active_alerts)
    }

    print("[Workflow] Analysis complete!")
    return final_report, preliminary_results


@app.route('/')
def index():
    """
    首页路由
    返回主页面
    """
    return render_template('index.html')


@app.route('/api/analyze')
def analyze():
    """
    分析API接口 - 智能体编排工作流
    1. 快速初筛（情感分析 + 风险矩阵）
    2. 中高风险触发深度分析（EL/VaR）
    3. 动态预警 + 结构化报告

    访问地址: http://localhost:5000/api/analyze
    """
    try:
        # 第1步：获取新闻（限制300秒超时，启用缓存）
        print("Fetching news (timeout: 300s, cache: enabled)...")
        fetcher = NewsFetcher(use_cache=True)
        articles = fetcher.fetch_news(days_back=30, max_time=300, filter_brand=True, use_cache=True)

        if not articles:
            return jsonify({
                "success": False,
                "error": "未能获取到新闻数据"
            }), 500

        print(f"Fetched {len(articles)} articles, starting agent orchestration analysis...")

        # 第2步：执行智能体编排工作流
        report, _ = workflow_analyze(articles)

        # 第3步：保存到历史记录
        print("Saving to history records...")
        history_manager.add_record("IF椰子水", report)

        # 返回分析结果
        return jsonify({
            "success": True,
            "data": report
        })

    except Exception as e:
        import traceback
        print(f"Analysis error: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"分析失败: {str(e)}"
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    获取历史记录列表
    返回最近5条分析历史
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        records = history_manager.get_recent_records(limit)
        return jsonify({
            "success": True,
            "data": records,
            "count": len(records)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/history/<record_id>', methods=['GET'])
def get_history_detail(record_id):
    """
    获取单条历史记录详情
    """
    try:
        detail = history_manager.get_record_detail(record_id)
        if detail:
            return jsonify({
                "success": True,
                "data": detail
            })
        else:
            return jsonify({
                "success": False,
                "error": "记录不存在"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/history/save', methods=['POST'])
def save_history():
    """
    保存当前分析结果到历史记录
    """
    try:
        data = request.json
        keyword = data.get('keyword', 'IF椰子水')
        analysis_data = data.get('analysis_data', {})

        record_id = history_manager.add_record(keyword, analysis_data)
        return jsonify({
            "success": True,
            "record_id": record_id,
            "message": "历史记录保存成功"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/health')
def health_check():
    """
    健康检查接口
    用于确认服务是否正常运行
    """
    return jsonify({
        "status": "ok",
        "message": "风险哨兵智能体运行正常"
    })


@app.route('/api/alerts')
def get_alerts():
    """
    获取实时预警列表
    """
    return jsonify({
        "success": True,
        "data": active_alerts,
        "count": len(active_alerts)
    })


@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """
    清除所有预警
    """
    active_alerts.clear()
    return jsonify({
        "success": True,
        "message": "预警已清除"
    })


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """
    清除新闻缓存，强制重新抓取
    """
    try:
        fetcher = NewsFetcher()
        fetcher.clear_cache()
        return jsonify({
            "success": True,
            "message": "新闻缓存已清除，下次分析将重新抓取"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/ecommerce/monitor')
def ecommerce_monitor_api():
    """
    电商监控API - 获取IF椰子水全平台电商数据
    """
    try:
        overview = ecommerce_monitor.get_product_overview()
        competitors = ecommerce_monitor.get_competitor_analysis()
        prices = ecommerce_monitor.get_price_monitoring()

        return jsonify({
            "success": True,
            "data": {
                "overview": overview,
                "competitors": competitors,
                "prices": prices,
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/enterprise/monitor')
def enterprise_monitor_api():
    """
    企业风险监控API - 获取天眼查/裁判文书等企业风险数据
    """
    try:
        report = enterprise_monitor.get_full_report()
        return jsonify({
            "success": True,
            "data": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/financial/monitor')
def financial_monitor_api():
    """
    财务风险监控API - IFBH(6603.HK)股价+财务健康度+反常信号检测
    """
    try:
        report = financial_monitor.get_full_report()
        return jsonify({
            "success": True,
            "data": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/policy/monitor')
def policy_monitor_api():
    """
    政策红线预警API - IF椰子水适用的法规全景+合规缺口+执法风险
    """
    try:
        report = policy_monitor.get_full_report()
        alerts = RegulatoryAlertGenerator.generate(report)
        return jsonify({
            "success": True,
            "data": report,
            "alerts": alerts,
            "alert_count": len(alerts),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/report/weekly')
def weekly_report_api():
    """
    自动周报生成API — 聚合所有监控模块，生成结构化周报
    """
    try:
        report = weekly_report_generator.generate()
        return jsonify({
            "success": True,
            "data": report
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/response/plan')
def response_plan_api():
    """
    风险应对引擎API - 根据当前所有风险信号生成综合应对方案
    自动聚合：舆情分析 + 定量风险 + 电商数据 + 企业风险
    """
    try:
        # 1. 获取舆情风险信号
        print("[ResponseAPI] Aggregating risk signals...")
        fetcher = NewsFetcher(use_cache=True)
        articles = fetcher.fetch_news(days_back=30, max_time=300, filter_brand=True)

        from risk_analyzer import PortfolioRiskAnalyzer
        risk_report = PortfolioRiskAnalyzer().analyze_portfolio(articles)

        # 2. 获取定量风险信号
        from quantitative_risk import calculate_EL, calculate_simple_VaR, stress_test, scenario_analysis
        sentiment_scores = []
        for item in risk_report.get("analyzed_articles", []):
            sentiment_scores.append(item.get("sentiment", {}).get("polarity", 0))

        depth_articles = [
            r for r in risk_report.get("analyzed_articles", [])
            if r.get("risk_level") in ("高", "中")
        ] or risk_report.get("analyzed_articles", [])

        # 获取财务数据用于EL调整
        fin_data = financial_monitor.get_full_report()

        el_result = calculate_EL(depth_articles, sentiment_scores, fin_data) if sentiment_scores else {"EL": 0, "PD": 0, "LGD": 0}
        var_result = calculate_simple_VaR(sentiment_scores) if sentiment_scores else {"VaR": 0}
        stress_result = stress_test(depth_articles, sentiment_scores, fin_data)

        # 3. 获取电商信号
        ecom_data = ecommerce_monitor.get_product_overview()
        competitor_data = ecommerce_monitor.get_competitor_analysis()

        # 4. 获取企业风险信号
        enterprise_data = enterprise_monitor.get_full_report()

        # 5. 聚合所有信号
        # 卡脖子信号：来自企业风险数据 + 供应链数据
        bottleneck_signals = {
            "overall_level": "critical",  # IF椰子水：100%单品种+100%单采购商+100%代工
            "supplier_risks": enterprise_data.get("supplier_risks", {}),
        }

        all_signals = {
            "risk_analysis": risk_report,
            "quantitative": {
                "EL": el_result,
                "VaR": var_result,
                "stress_test": stress_result,
                "scenario_analysis": scenario_analysis(
                    depth_articles, sentiment_scores, fin_data
                ) if sentiment_scores else None,
            },
            "ecommerce": {
                "overview": ecom_data,
                "competitors": competitor_data,
            },
            "enterprise": enterprise_data,
            "bottleneck": bottleneck_signals,
        }

        # 6. 生成综合应对方案
        print("[ResponseAPI] Generating response plan...")
        plan = response_engine.generate_full_response_plan(all_signals)

        return jsonify({
            "success": True,
            "data": plan,
            "signal_summary": {
                "risk_score": risk_report.get("average_risk_score", 0),
                "risk_level": risk_report.get("overall_risk_level", "未知"),
                "el_value": el_result.get("EL", 0),
                "crisis_level": plan["crisis_assessment"]["level"],
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/delphi-analyze', methods=['GET'])
def delphi_analyze():
    """
    德尔菲风险分析API接口
    执行3轮专家共识评估，返回结构化报告

    访问地址: http://localhost:5000/api/delphi-analyze
    """
    try:
        # 1. 导入德尔菲分析器
        import sys
        sys.path.insert(0, 'C:/Users/23994/.claude/skills/delphi-risk')
        from delphi_analyzer import DelphiAnalyzer

        # 2. 获取新闻数据（优先用缓存，10秒超时，避免重复抓取）
        print("[Delphi] Fetching news (cache-first, timeout=10s)...")
        fetcher = NewsFetcher(use_cache=True)
        articles = fetcher.fetch_news(days_back=30, max_time=10, use_cache=True)

        if not articles:
            return jsonify({
                "success": False,
                "error": "未能获取到新闻数据"
            }), 500

        print(f"[Delphi] Fetched {len(articles)} articles")

        # 3. 准备新闻数据（提取情感分数和风险关键词）
        analyzer = RiskAnalyzer()
        news_list = []

        for article in articles:
            result = analyzer.analyze_article(article)

            # 提取风险关键词
            risk_keywords = []
            for risk in result['risks']:
                risk_keywords.extend(risk['keywords_found'])

            news_item = {
                'title': article['title'],
                'sentiment_score': result['sentiment']['polarity'],
                'risk_keywords': risk_keywords,
                'source': article['source']
            }
            news_list.append(news_item)

        # 4. 执行德尔菲分析
        print("[Delphi] Starting 3-round expert evaluation...")
        delphi = DelphiAnalyzer()
        results = delphi.analyze(news_list)

        # 5. 生成结构化报告
        report = {
            "title": "德尔菲风险分析报告",
            "generated_at": datetime.now().isoformat(),
            "methodology": {
                "name": "Delphi Method",
                "rounds": 3,
                "experts": [
                    {"name": "法律专家", "focus": "诉讼、召回、违规、处罚"},
                    {"name": "市场专家", "focus": "销售、竞争、下滑、亏损"},
                    {"name": "声誉专家", "focus": "消费者、安全、质量、投诉"}
                ],
                "scoring_rules": {
                    "base_score": "sentiment < -0.6: 4分, < -0.3: 3分, < 0: 2分, >= 0: 1分",
                    "weighting": "匹配专家关键词 +1分",
                    "final_level": "1-2分: 低, 2.1-3分: 中, 3.1-5分: 高"
                }
            },
            "summary": {
                "total_news": len(articles),
                "analyzed_top": len(results),
                "high_risk_count": sum(1 for r in results if r['final_risk_level'] == '高'),
                "medium_risk_count": sum(1 for r in results if r['final_risk_level'] == '中'),
                "low_risk_count": sum(1 for r in results if r['final_risk_level'] == '低')
            },
            "results": results,
            "consensus_statistics": {
                "average_score": round(sum(r['consensus_score'] for r in results) / len(results), 2) if results else 0,
                "average_iqr": round(sum(r['iqr'] for r in results) / len(results), 2) if results else 0,
                "consensus_rate": "100%" if all(r['iqr'] <= 1.5 for r in results) else f"{sum(1 for r in results if r['iqr'] <= 1.5)}/{len(results)}"
            }
        }

        print("[Delphi] Analysis complete!")

        return jsonify({
            "success": True,
            "data": report
        })

    except Exception as e:
        import traceback
        print(f"[Delphi] Analysis failed: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"德尔菲分析失败: {str(e)}"
        }), 500


@app.route('/api/mcp/warehouse/stats', methods=['GET'])
def mcp_warehouse_stats():
    """
    MCP数据仓库统计接口
    返回全量数据采集的统计信息
    """
    try:
        from mcp_data_warehouse import MCPDataWarehouse
        warehouse = MCPDataWarehouse()
        stats = warehouse.get_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/warehouse/logs', methods=['GET'])
def mcp_collection_logs():
    """
    MCP采集日志接口
    """
    try:
        from mcp_data_warehouse import MCPDataWarehouse
        limit = request.args.get('limit', 10, type=int)
        warehouse = MCPDataWarehouse()
        logs = warehouse.get_collection_logs(limit)
        return jsonify({
            "success": True,
            "data": logs,
            "count": len(logs)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/warehouse/query', methods=['POST'])
def mcp_warehouse_query():
    """
    MCP数据仓库查询接口
    支持自定义SQL查询
    """
    try:
        from mcp_data_warehouse import MCPDataWarehouse
        data = request.json
        sql = data.get('sql', '')
        params = data.get('params', [])

        if not sql:
            return jsonify({
                "success": False,
                "error": "SQL语句不能为空"
            }), 400

        warehouse = MCPDataWarehouse()
        results = warehouse.mcp_query(sql, tuple(params) if params else None)
        return jsonify({
            "success": True,
            "data": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/full-collection', methods=['POST'])
def mcp_full_collection():
    """
    MCP全量数据采集接口
    触发全量/增量数据采集
    """
    try:
        from mcp_news_fetcher import MCPNewsFetcher

        data = request.json or {}
        days_back = data.get('days_back', 30)
        force_full = data.get('force_full', False)

        fetcher = MCPNewsFetcher()

        # 执行采集
        articles = fetcher.fetch_news(days_back=days_back, use_cache=not force_full)

        # 获取最新统计
        stats = fetcher.get_warehouse_stats()

        return jsonify({
            "success": True,
            "data": {
                "collection_status": "completed",
                "records_collected": len(articles),
                "warehouse_stats": stats
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def open_browser(delay=3):
    """
    延迟几秒后自动打开浏览器
    """
    def _open():
        time.sleep(delay)
        url = "http://localhost:5000"
        print(f"\n[Browser] Opening {url} ...")
        try:
            webbrowser.open(url)
            print("[Browser] Opened successfully!")
        except Exception as e:
            print(f"[Browser] Failed to open: {e}")
            print(f"[Browser] Please manually visit: {url}")

    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


# 主程序入口
if __name__ == '__main__':
    print("=" * 50)
    print("[ROBOT] Risk Sentinel Agent Starting...")
    print("=" * 50)
    print("Access: http://localhost:5000")
    print("API: http://localhost:5000/api/analyze")
    print("News fetch timeout: 300 seconds")
    print("=" * 50)

    # 自动打开浏览器
    open_browser(delay=3)

    # 启动Flask服务器
    # debug=True: 开启调试模式，代码修改后自动重启
    # host='0.0.0.0': 允许外部访问
    # port=5000: 端口号
    app.run(debug=True, host='0.0.0.0', port=5000)
