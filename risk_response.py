"""
risk_response.py - 风险应对引擎

根据风险信号自动生成多维度应对方案：
1. 供应链中断应对（备选供应商、库存策略、合同调整）
2. 品牌危机公关（声明等级、响应时机、渠道策略）
3. 法律合规整改（应诉策略、标签审查、合规清单）
4. 市场份额保卫（促销方案、渠道调整、产品召回决策）
5. 财务风险对冲（保险建议、损失准备金、现金流管理）

核心逻辑：风险信号 → 影响评估 → 应对方案 → 优先级排序
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class RiskResponseEngine:
    """风险应对引擎"""

    def __init__(self):
        self.response_playbook = self._load_playbook()

    def _load_playbook(self) -> Dict:
        """加载应对策略库"""
        return {
            "supply_chain": {
                "triggers": ["supply_chain_risk", "price_anomaly", "customs_risk"],
                "response_templates": self._supply_chain_playbook(),
            },
            "brand_crisis": {
                "triggers": ["negative_review_surge", "social_sentiment_crisis", "rating_drop"],
                "response_templates": self._brand_crisis_playbook(),
            },
            "legal_compliance": {
                "triggers": ["regulatory_risk", "litigation_risk"],
                "response_templates": self._legal_compliance_playbook(),
            },
            "market_share": {
                "triggers": ["sales_decline", "competitive_threat"],
                "response_templates": self._market_defense_playbook(),
            },
            "bottleneck": {
                "triggers": ["supplier_dependency", "single_source", "talent_loss", "tech_bottleneck"],
                "response_templates": self._bottleneck_playbook(),
            },
            "financial": {
                "triggers": ["financial_risk", "supply_chain_risk"],
                "response_templates": self._financial_playbook(),
            },
        }

    # ============ 供应链应对策略库 ============

    def _supply_chain_playbook(self) -> Dict:
        return {
            "alternative_suppliers": [
                {
                    "supplier": "Thai Agri Foods (泰国农业食品)",
                    "location": "泰国春蓬府",
                    "capacity": "年产能50万吨椰子",
                    "certification": "FDA/GMP/HACCP",
                    "lead_time_days": 45,
                    "price_premium": "+8%",
                    "reliability_score": 85,
                    "contact_note": "已建立初步联系，可快速启动供应协议",
                },
                {
                    "supplier": "Siam Coconut Co. (暹罗椰子公司)",
                    "location": "泰国叻丕府",
                    "capacity": "年产能30万吨椰子",
                    "certification": "FDA/ISO22000",
                    "lead_time_days": 35,
                    "price_premium": "+5%",
                    "reliability_score": 90,
                    "contact_note": "IF现有供应商的备选，地理位置接近",
                },
                {
                    "supplier": "Philippine Coconut Authority",
                    "location": "菲律宾奎松省",
                    "capacity": "年产能100万吨椰子",
                    "certification": "FDA/Organic",
                    "lead_time_days": 50,
                    "price_premium": "+3%",
                    "reliability_score": 78,
                    "contact_note": "成本最优方案，但需额外海关手续",
                },
            ],
            "inventory_strategies": {
                "current_level": "30天安全库存（推测）",
                "recommended_level": "60天安全库存",
                "reason": "泰国干旱风险概率65%、海运不确定性增加",
                "cost_estimate": "增加库存持有成本约15万/月（仓储+资金占用）",
                "implementation": "分2批补货：第一批14天内补至45天，第二批30天内补至60天",
            },
            "contract_adjustments": [
                {
                    "clause": "原材料价格浮动条款",
                    "current": "无",
                    "recommended": "约定椰子采购价上限，超出部分供应商承担30%",
                    "urgency": "high",
                },
                {
                    "clause": "供应中断赔偿条款",
                    "current": "标准不可抗力",
                    "recommended": "约定供应商中断超过7天需按日赔偿订单额的2%",
                    "urgency": "medium",
                },
                {
                    "clause": "质量保障条款",
                    "current": "基本质量标准",
                    "recommended": "增加第三方定期抽检机制，每批次附SGS检测报告",
                    "urgency": "high",
                },
            ],
        }

    # ============ 品牌危机应对策略库 ============

    def _brand_crisis_playbook(self) -> Dict:
        return {
            "response_levels": {
                "黄色预警": {
                    "condition": "负面舆情占比30-50%",
                    "response_time": "48小时内",
                    "actions": ["内部调查启动", "客服话术统一", "社交媒体监控加强"],
                },
                "橙色预警": {
                    "condition": "负面舆情占比50-70% 且出现产品召回",
                    "response_time": "24小时内",
                    "actions": ["公开发布声明", "CEO出面回应", "第三方检测机构介入", "临时下架问题批次"],
                },
                "红色预警": {
                    "condition": "负面舆情占比>70% 或监管部门介入",
                    "response_time": "6小时内",
                    "actions": ["紧急新闻发布会", "全面产品召回", "CEO公开道歉", "成立危机处理小组", "聘请外部公关顾问"],
                },
            },
            "statement_templates": {
                "acknowledge": "承认问题存在，表达歉意，承诺调查——适用于质量问题已被证实",
                "clarify": "澄清事实，提供检测报告证据——适用于指控不实或存在误解",
                "deflect": "转移焦点至行业问题，强调品牌历史信誉——适用于行业普遍问题波及",
                "commit": "提出具体整改措施和时间表——适用于需要重建信任阶段",
            },
            "channel_strategy": {
                "priority_sequence": ["官方微博/公众号", "天猫/京东店铺公告", "媒体通稿", "KOL合作", "消费者热线/客服"],
                "key_message": "IF椰子水始终将消费者健康放在首位，我们已启动全面调查",
                "avoid": ["沉默不回应", "与消费者对骂", "甩锅供应商", "删除差评"],
            },
        }

    # ============ 法律合规应对策略库 ============

    def _legal_compliance_playbook(self) -> Dict:
        return {
            "label_compliance": {
                "issue": "进口食品中文标签不合规",
                "root_cause": "营养成分表标注值与检测值不符",
                "fix_actions": [
                    "聘请第三方检测机构对全批次产品重新检测",
                    "更新中文标签模板，确保营养成分表准确",
                    "建立进口前标签预审核流程（需3个工作日）",
                ],
                "estimated_cost": "3-5万元（含检测费、标签重印费）",
                "timeline": "2周内完成整改",
            },
            "license_management": {
                "issue": "食品经营许可证到期未续",
                "fix_actions": [
                    "立即续期食品经营许可证",
                    "建立证照到期自动提醒系统（提前90天）",
                    "排查所有关联证照有效期",
                ],
                "estimated_cost": "0.5万元（含加急办理费）",
                "timeline": "5个工作日",
            },
            "litigation_response": {
                "active_cases": [
                    {
                        "case": "产品责任纠纷（消费者诉腹泻）",
                        "strategy": "积极应诉 + 主动和解",
                        "reason": "诉讼成本高于和解成本，且公开判决可能引发连锁诉讼",
                        "estimated_settlement": "3-5万元",
                        "prevention": "建立批次追溯系统，快速定位问题产品",
                    },
                ],
                "defense_strategy": "建立证据链：原材料采购记录→生产日期→检测报告→进口报关单→销售记录",
            },
        }

    # ============ 市场保卫战策略库 ============

    def _market_defense_playbook(self) -> Dict:
        return {
            "pricing_response": {
                "current_situation": "均价86元，较历史下降6.7%，部分经销商降价10-15%",
                "recommended_action": "维持当前价格，避免大幅降价",
                "reason": "降价会进一步损害品牌高端形象，且竞品Vita Coco也在79-99元区间",
                "alternative": "推出'品质承诺装'附赠SGS检测报告，以价值替代价格竞争",
            },
            "product_recall_decision": {
                "if_quality_confirmed": {
                    "action": "立即召回涉事批次（约10万箱），公开道歉",
                    "cost_estimate": "直接损失约890万元（含召回物流+退款+品牌折损）",
                    "benefit": "终止负面舆情扩散，为品牌重建奠定基础",
                },
                "if_quality_unconfirmed": {
                    "action": "发布SGS检测报告，邀请媒体见证检测过程",
                    "cost_estimate": "约15万元（检测+媒体沟通）",
                    "benefit": "用事实反击谣言，转化舆情危机为品牌信任建立机会",
                },
            },
            "channel_strategy": {
                "offline": "加强与山姆、盒马、Ole等高端渠道合作，强化品质定位",
                "online": "天猫旗舰店设置'品质溯源'专区，展示泰国产地实拍",
                "new_channels": "考虑Costco、叮咚买菜等新兴渠道拓展",
            },
        }

    # ============ 卡脖子风险策略库（PDF Module 6）============

    def _bottleneck_playbook(self) -> Dict:
        """
        IF椰子水"卡脖子"风险数据库
        ——完全对齐PDF Module 6: 硬科技的"技术壁垒"与"卡脖子"风险

        IF的"卡脖子"不同于芯片行业的专利壁垒，而是：
        1. 原料端：100%依赖泰国Nam Hom香水椰（保护品种，禁止出口树苗）
        2. 采购端：100%通过关联方General Beverage（创始人兄弟控股公司）
        3. 生产端：100%外包给12家代工厂（前5大占96.9%）
        4. 人才端：全球仅46名员工，CEO持股65.51%不可替代
        5. 市场端：90.4%收入来自中国单一市场
        """
        return {
            "supply_bottlenecks": {
                "raw_material": {
                    "item": "泰国Nam Hom香水椰",
                    "dependency_level": "absolute",
                    "dependency_detail": (
                        "100%原料来自泰国Nam Hom香水椰品种，产地在叻丕府（80%）+龙仔厝府。"
                        "该品种树苗已被泰国政府列为保护品种、禁止出口。"
                        "IFBH消耗量占泰国椰子水总产量的50%以上。"
                        "全球替代品：印尼椰子（甜度低、无奶香味）、菲律宾椰子（产量大但品质差异显著）。"
                    ),
                    "single_point_failure": (
                        "泰国干旱/洪水/病虫害 → 香水椰减产 → IFBH无替代原料 → 生产线停摆"
                    ),
                    "disruption_scenarios": [
                        {"scenario": "泰国极端干旱", "probability": 0.65,
                         "impact": "椰子减产12-20%，原材料成本上涨30-50%",
                         "recovery_time": "6-12个月（等待下一个种植季）"},
                        {"scenario": "泰国政府限制椰子水出口", "probability": 0.15,
                         "impact": "出口配额削减或加征关税，供应量骤降",
                         "recovery_time": "不确定，取决于政策走向"},
                        {"scenario": "Nam Hom品种病虫害", "probability": 0.10,
                         "impact": "大规模椰子树死亡，恢复周期3-5年",
                         "recovery_time": "3-5年（重新种植成长期）"},
                        {"scenario": "海运中断（红海/马六甲）", "probability": 0.30,
                         "impact": "运输时间延长2-3倍，运费上涨50-100%",
                         "recovery_time": "1-3个月"},
                    ],
                },
                "procurement": {
                    "item": "General Beverage (关联方采购)",
                    "dependency_level": "near_absolute",
                    "dependency_detail": (
                        "2025年前：General Beverage(GB)是IFBH的唯一一般采集商，"
                        "100%的椰子水原料通过GB采购。GB创始人与IFBH创始人为同一家族。"
                        "GB从仅2位采集商+33位农户处收集原料。"
                    ),
                    "mitigation_plan": {
                        "2025年底目标": "GB占比降至70%（新增3家采集商）",
                        "2027年目标": "GB占比降至50%以下",
                        "current_status": "正在推进中，但过渡期仍高度依赖GB",
                    },
                    "single_point_failure": (
                        "GB因关联交易审查/财务问题/家族纠纷而中断供应 → IFBH直接断料"
                    ),
                },
                "manufacturing": {
                    "item": "12家代工厂（前5大占96.9%）",
                    "dependency_level": "high",
                    "dependency_detail": (
                        "IFBH无自有工厂，100%生产外包给12家代工厂。"
                        "前五大代工厂贡献96.9%的产量。"
                        "任何一家主要代工厂停产，产能将受到严重影响。"
                    ),
                },
            },
            "talent_bottlenecks": {
                "key_person_risk": {
                    "person": "Pongsakorn Pongsak (创始人兼CEO)",
                    "shareholding": "65.51%",
                    "irreplaceability": "critical",
                    "detail": (
                        "CEO同时控制IFBH（品牌方）和General Beverage（原料供应方），"
                        "是整个商业模式的唯一纽带。一人身兼：品牌战略决策者、"
                        "核心供应商实控人、产品配方最终审批人。"
                    ),
                    "loss_scenarios": [
                        {"scenario": "CEO健康问题/意外", "probability": 0.05,
                         "impact": "股价暴跌50%+、供应链断裂、战略决策真空",
                         "mitigation": "建立CEO继任计划、关键决策权分散至董事会"},
                        {"scenario": "CEO法律风险（关联交易调查）", "probability": 0.20,
                         "impact": "港交所/证监会调查、品牌声誉二次打击",
                         "mitigation": "规范GB与IFBH的关联交易定价机制"},
                    ],
                },
                "team_concentration": {
                    "total_employees": 46,
                    "distribution": {
                        "销售": 20,
                        "研发(R&D)": 5,
                        "仓储物流": 15,
                        "行政后台": 6,
                    },
                    "key_risk": (
                        "仅5名研发人员掌控产品配方和品控标准。"
                        "任何一名核心技术人员的流失都可能导致配方泄露或品控下降。"
                    ),
                },
            },
            "alternative_supplier_assessment": {
                "switching_cost_estimate": {
                    "raw_material_switch": {
                        "from": "泰国Nam Hom香水椰",
                        "to_candidates": [
                            {
                                "source": "印尼椰子",
                                "feasibility": "partial",
                                "quality_gap": "甜度下降40%、无奶香味→产品口感将显著变化",
                                "cost_change": "原材料成本-15%（但品牌溢价能力可能下降30%+）",
                                "lead_time": "3-6个月（建立新采购网络）",
                                "risk": "消费者口感差异投诉激增→可能引发新一轮品牌危机",
                            },
                            {
                                "source": "菲律宾椰子",
                                "feasibility": "partial",
                                "quality_gap": "甜度下降30%、风味偏淡",
                                "cost_change": "原材料成本-25%",
                                "lead_time": "4-8个月",
                                "risk": "菲律宾台风频发，供应稳定性不如泰国",
                            },
                            {
                                "source": "越南椰子",
                                "feasibility": "low",
                                "quality_gap": "品种差异大、接近度低",
                                "cost_change": "成本+10%（物流+品质筛选）",
                                "lead_time": "12个月+",
                                "risk": "品质一致性难以保证",
                            },
                        ],
                        "estimated_total_switching_cost": "500万-1200万元（含新供应商审核、品质测试、配方调整、消费者测试、标签更新）",
                        "switching_timeline": "6-18个月（取决于目标替代比例）",
                    },
                    "procurement_switch": {
                        "from": "General Beverage (关联方)",
                        "to_candidates": [
                            {
                                "source": "直接与泰国农户/合作社签约",
                                "feasibility": "medium",
                                "challenge": "需要建立泰国本地采购团队（IFBH目前无此能力）",
                                "cost_change": "采购成本可能上升10-20%（失去GB的规模效应）",
                                "lead_time": "12-18个月",
                            },
                            {
                                "source": "泰国其他采集商",
                                "feasibility": "medium",
                                "challenge": "泰国椰子采集市场高度分散，需要整合多家小型采集商",
                                "cost_change": "采购成本基本持平",
                                "lead_time": "6-12个月",
                            },
                        ],
                        "estimated_total_switching_cost": "200万-500万元（含团队建设、供应商开发、法律合规）",
                        "switching_timeline": "6-18个月",
                    },
                    "manufacturing_switch": {
                        "from": "现有12家代工厂",
                        "to_candidates": [
                            {
                                "source": "中国境内代工厂（如统一、康师傅等）",
                                "feasibility": "medium",
                                "challenge": "需要将泰国椰子水原液进口到中国灌装（涉及海关+检验检疫），流程复杂",
                                "cost_change": "运输成本+15%、关税+灌装成本 vs 泰国代工费节省",
                                "lead_time": "6-12个月",
                            },
                        ],
                        "estimated_total_switching_cost": "300万-800万元",
                        "switching_timeline": "6-12个月",
                    },
                },
            },
            "bottleneck_risk_score": {
                "raw_material_dependency": {"score": 95, "level": "critical",
                    "detail": "100%依赖单一品种、单一国家、单一产区"},
                "procurement_dependency": {"score": 85, "level": "critical",
                    "detail": "100%通过单一关联方采购，无独立采购能力"},
                "manufacturing_dependency": {"score": 70, "level": "high",
                    "detail": "100%外包、前5大代工厂占96.9%"},
                "talent_concentration": {"score": 80, "level": "critical",
                    "detail": "CEO一人身兼品牌方+供应方实控人、仅5名研发、46名员工"},
                "market_concentration": {"score": 75, "level": "high",
                    "detail": "中国单一市场贡献90.4%收入"},
                "overall_bottleneck_score": 81,
                "overall_level": "critical",
            },
        }

    # ============ 财务风险应对策略库 ============

    def _financial_playbook(self) -> Dict:
        return {
            "loss_reserve": {
                "recommended_reserve": "200-300万元",
                "coverage": "预期应对未来6个月的法律诉讼、产品召回、品牌修复费用",
                "source": "从营销预算中调拨30%，从利润留存中提取",
            },
            "insurance": {
                "product_recall_insurance": "建议投保500万元产品召回险，年费约8-12万元",
                "product_liability_insurance": "建议提升至1000万元保额，年费约15万元",
            },
            "cash_flow_management": {
                "receivable_acceleration": "经销商账款从45天缩短至30天",
                "inventory_optimization": "安全库存增加至60天但通过VMI模式降低资金占用",
            },
        }

    # ============ 核心方法：综合应对方案生成 ============

    def generate_full_response_plan(self, signals: Dict) -> Dict:
        """
        主入口：根据综合风险信号生成完整应对方案

        Args:
            signals: 包含以下来源的风险信号字典
                - risk_analysis: risk_analyzer 输出
                - quantitative: quantitative_risk 输出
                - ecommerce: ecommerce_monitor 输出
                - enterprise: enterprise_monitor 输出

        Returns:
            完整的结构化应对方案
        """
        print("[ResponseEngine] Generating full response plan...")

        # 1. 评估当前危机等级
        crisis_level = self._assess_crisis_level(signals)

        # 2. 按风险维度生成应对方案
        supply_plan = self.generate_supply_chain_response(signals)
        brand_plan = self.generate_brand_crisis_response(signals)
        legal_plan = self.generate_legal_response(signals)
        market_plan = self.generate_market_response(signals)
        bottleneck_plan = self.generate_bottleneck_response(signals)
        financial_plan = self.generate_financial_response(signals)

        # 3. 汇总所有行动项并排序
        all_actions = self._collect_all_actions(
            supply_plan, brand_plan, legal_plan, market_plan, bottleneck_plan, financial_plan
        )
        prioritized = self._prioritize_actions(all_actions, crisis_level)

        # 4. 计算总成本估算
        total_cost = self._estimate_total_cost(prioritized)

        # 5. 生成执行时间线
        timeline = self._generate_timeline(prioritized, crisis_level)

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "engine_version": "2.0",
                "crisis_level": crisis_level,
                "response_mode": "immediate" if crisis_level == "red" else "planned",
            },
            "executive_summary": self._generate_executive_summary(
                crisis_level, prioritized, total_cost
            ),
            "crisis_assessment": crisis_level,
            "response_plans": {
                "supply_chain": supply_plan,
                "brand_crisis": brand_plan,
                "legal_compliance": legal_plan,
                "market_defense": market_plan,
                "bottleneck": bottleneck_plan,
                "financial": financial_plan,
            },
            "prioritized_actions": prioritized,
            "cost_estimate": total_cost,
            "timeline": timeline,
        }

    def _assess_crisis_level(self, signals: Dict) -> Dict:
        """评估当前危机等级"""
        score = 0

        # 风险评分（来自 risk_analyzer）
        risk_data = signals.get("risk_analysis", {})
        avg_score = risk_data.get("average_risk_score", 0)
        if avg_score > 80:
            score += 30
        elif avg_score > 60:
            score += 20
        elif avg_score > 40:
            score += 10

        # 定量风险（EL值）
        quant = signals.get("quantitative", {})
        el_data = quant.get("EL", {})
        el_value = el_data.get("EL", 0)
        if el_value > 15:
            score += 25
        elif el_value > 8:
            score += 15

        # 电商信号
        ecom = signals.get("ecommerce", {})
        overview = ecom.get("overview", {})
        platforms = overview.get("platforms", {})
        tmall = platforms.get("tmall", {})
        if tmall.get("sales_change_pct", 0) < -10:
            score += 15
        if tmall.get("avg_rating", 5) < 4.5:
            score += 10

        # 企业风险信号
        enterprise = signals.get("enterprise", {})
        enterprise_score = enterprise.get("risk_score", {}).get("total_score", 100)
        if enterprise_score < 45:
            score += 20
        elif enterprise_score < 65:
            score += 10

        # 社交媒体信号
        social = tmall.get("review_keywords", [])
        negative_count = sum(1 for k in social if k.get("sentiment") == "negative")
        if negative_count > 5:
            score += 10

        # 卡脖子瓶颈信号（PDF Module 6）
        bottleneck = signals.get("bottleneck", {})
        bottleneck_score = bottleneck.get("overall_level", "low")
        if bottleneck_score == "critical":
            score += 25
        elif bottleneck_score == "high":
            score += 15
        elif bottleneck_score == "medium":
            score += 8

        # 判定等级
        if score >= 60:
            level = "red"
            description = "红色预警：多维度风险同时触发，需立即启动全面危机应对"
        elif score >= 35:
            level = "orange"
            description = "橙色预警：多个风险领域出现恶化信号，需紧急响应"
        elif score >= 20:
            level = "yellow"
            description = "黄色预警：存在风险信号但可控，建议48小时内启动应对"
        else:
            level = "green"
            description = "绿色：风险可控，保持常规监控即可"

        return {"level": level, "score": score, "description": description}

    def generate_supply_chain_response(self, signals: Dict) -> Dict:
        """供应链中断应对方案"""
        enterprise = signals.get("enterprise", {})
        supplier_risks = enterprise.get("supplier_risks", {}).get("raw_coconut_supply", {})
        risks = supplier_risks.get("risks", [])

        playbook = self._supply_chain_playbook()

        # 计算供应中断概率
        disruption_probs = [r.get("probability", 0) for r in risks]
        avg_disruption_prob = sum(disruption_probs) / len(disruption_probs) if disruption_probs else 0

        # 根据概率选择应对强度
        if avg_disruption_prob > 0.5:
            action_level = "immediate"
            recommended_suppliers = playbook["alternative_suppliers"]
            inventory_action = playbook["inventory_strategies"]
        else:
            action_level = "prepare"
            recommended_suppliers = playbook["alternative_suppliers"][:1]
            inventory_action = {
                "recommended_level": "45天安全库存",
                "implementation": "30天内逐步补货至45天",
            }

        return {
            "risk_assessment": {
                "disruption_probability": round(avg_disruption_prob, 2),
                "key_risk_factors": [r["type"] for r in risks],
                "action_level": action_level,
            },
            "alternative_suppliers": recommended_suppliers,
            "inventory_strategy": inventory_action,
            "contract_adjustments": playbook["contract_adjustments"],
            "price_monitoring": {
                "current_coconut_price": "约4800泰铢/吨",
                "alert_threshold": "上涨超过15%时触发预警",
                "recommendation": "建议签订3个月锁价合同以对冲价格风险",
            },
        }

    def generate_brand_crisis_response(self, signals: Dict) -> Dict:
        """品牌危机公关应对方案"""
        ecom = signals.get("ecommerce", {})
        overview = ecom.get("overview", {})
        platforms = overview.get("platforms", {})
        tmall = platforms.get("tmall", {})
        social = platforms.get("social", {})

        playbook = self._brand_crisis_playbook()

        # 判断响应等级
        weibo_neg = social.get("weibo", {}).get("sentiment_ratio", {}).get("negative", 0)
        avg_rating = tmall.get("avg_rating", 5)
        neg_ratio = tmall.get("negative_review_ratio", 0)

        if weibo_neg > 0.5 and neg_ratio > 0.1:
            response_level = "红色预警"
        elif weibo_neg > 0.4 or neg_ratio > 0.08:
            response_level = "橙色预警"
        else:
            response_level = "黄色预警"

        level_config = playbook["response_levels"].get(response_level, {})

        # 选择声明策略
        if avg_rating < 4.3:
            statement_strategy = "acknowledge"
        elif avg_rating < 4.6:
            statement_strategy = "commit"
        else:
            statement_strategy = "clarify"

        return {
            "crisis_level": response_level,
            "response_deadline": level_config.get("response_time", "48小时"),
            "immediate_actions": level_config.get("actions", []),
            "statement_strategy": {
                "type": statement_strategy,
                "template": playbook["statement_templates"].get(statement_strategy, ""),
                "draft_headline": self._generate_statement_headline(statement_strategy),
            },
            "channel_sequence": playbook["channel_strategy"]["priority_sequence"],
            "key_message": playbook["channel_strategy"]["key_message"],
            "avoid_actions": playbook["channel_strategy"]["avoid"],
            "metrics_to_track": [
                "微博话题阅读量（24小时）",
                "天猫旗舰店评分变化",
                "主流媒体报道倾向",
                "竞品反应动作",
            ],
        }

    def generate_legal_response(self, signals: Dict) -> Dict:
        """法律合规应对方案"""
        enterprise = signals.get("enterprise", {})
        indicators = enterprise.get("risk_indicators", {})
        china = indicators.get("China_agent", {}).get("indicators", {})

        playbook = self._legal_compliance_playbook()

        penalties = china.get("administrative_penalties", {}).get("recent", [])
        lawsuits = china.get("lawsuits", {}).get("recent", [])

        actions = []

        # 标签合规整改
        for penalty in penalties:
            if "标签" in penalty.get("detail", ""):
                actions.append(playbook["label_compliance"])

        # 许可证整改
        if any("许可证" in p.get("detail", "") for p in penalties):
            actions.append(playbook["license_management"])

        # 诉讼应对
        active_lawsuits = [l for l in lawsuits if l.get("status") == "审理中"]
        if active_lawsuits:
            actions.append({
                "active_litigation": active_lawsuits,
                "strategy": playbook["litigation_response"]["defense_strategy"],
                "recommendation": "评估和解可能性，避免判决引发连锁诉讼",
            })

        return {
            "risk_level": "high" if len(active_lawsuits) > 1 else "medium",
            "compliance_actions": actions,
            "estimated_total_legal_cost": "10-20万元（含诉讼费、和解费、合规整改费）",
            "timeline": "关键整改项2周内完成，诉讼预计3-6个月",
            "preventive_measures": [
                "建立进口食品标签预审核SOP",
                "聘请常年法律顾问（食品合规方向）",
                "每季度进行一次合规审计",
            ],
        }

    def generate_market_response(self, signals: Dict) -> Dict:
        """市场份额保卫方案"""
        ecom = signals.get("ecommerce", {})
        competitors = ecom.get("competitors", {})

        playbook = self._market_defense_playbook()

        # 是否触发召回决策
        risk_analysis = signals.get("risk_analysis", {})
        has_recall_risk = any(
            "recall" in str(r).lower() or "召回" in str(r)
            for r in risk_analysis.get("risk_type_summary", {}).keys()
        )

        return {
            "current_market_position": {
                "market_share": "14.2%（椰子水品类第2）",
                "trend": "正在流失3.5个百分点",
                "main_threat": "Vita Coco借IF危机获客",
            },
            "pricing_strategy": playbook["pricing_response"],
            "recall_decision": playbook["product_recall_decision"][
                "if_quality_confirmed" if has_recall_risk else "if_quality_unconfirmed"
            ],
            "channel_actions": playbook["channel_strategy"],
            "competitive_intelligence": {
                "vita_coco": "加大促销，建议避其锋芒，打品质差异牌",
                "new_entrants": "低价品牌冲击，建议推出'IF Fresh'子品牌覆盖中端市场",
            },
        }

    def generate_bottleneck_response(self, signals: Dict) -> Dict:
        """
        卡脖子风险分析 + 应对方案
        对齐PDF Module 6: 硬科技的"技术壁垒"与"卡脖子"风险
        IF椰子水的"技术"= Nam Hom香水椰品种 + 代工品控能力 + CEO家族供应链关系
        """
        playbook = self._bottleneck_playbook()
        bottlenecks = playbook["supply_bottlenecks"]
        talent = playbook["talent_bottlenecks"]
        switching = playbook["alternative_supplier_assessment"]
        scores = playbook["bottleneck_risk_score"]

        # 聚合来自各数据源的瓶颈信号
        enterprise = signals.get("enterprise", {})
        supplier_risks = enterprise.get("supplier_risks", {}).get("raw_coconut_supply", {})

        # 计算整体切换成本范围
        total_switching_low = 500 + 200 + 300  # 最低
        total_switching_high = 1200 + 500 + 800  # 最高

        return {
            "risk_assessment": {
                "overall_bottleneck_score": scores["overall_bottleneck_score"],
                "overall_level": scores["overall_level"],
                "dimension_scores": scores,
            },
            "supply_bottlenecks": {
                "raw_material": bottlenecks["raw_material"],
                "procurement": bottlenecks["procurement"],
                "manufacturing": bottlenecks["manufacturing"],
            },
            "talent_risk": talent,
            "switching_analysis": {
                "summary": switching,
                "total_cost_estimate": f"{total_switching_low}-{total_switching_high}万元",
                "total_timeline": "6-18个月（全面完成供应链去依赖化）",
                "recommended_sequence": [
                    {
                        "step": 1,
                        "action": "采购去依赖化（最紧迫）",
                        "target": "6个月内新增3家采集商，GB占比降至70%以下",
                        "cost": "200-500万元",
                        "rationale": "采购依赖是最大单点故障——GB一旦中断，IFBH直接断料。应最优先执行。",
                    },
                    {
                        "step": 2,
                        "action": "原料产地多元化",
                        "target": "12个月内建立印尼/菲律宾椰子水测试采购线",
                        "cost": "100-300万元（样品测试+小规模试产）",
                        "rationale": "Nam Hom香水椰的稀缺性决定了长期必须有多产地备份。短期内测试替代品种，长期建立稳定替代供应。",
                    },
                    {
                        "step": 3,
                        "action": "代工厂分散化",
                        "target": "将前5大代工厂产能占比从96.9%降至80%以下",
                        "cost": "300-800万元（新增代工厂审核+试产+品质验证）",
                        "rationale": "代工集中度风险相对可控（可切换性高于原料），但仍须建立冗余。",
                    },
                    {
                        "step": 4,
                        "action": "人才备份与继任计划",
                        "target": "建立CEO继任计划 + 研发团队扩至10人 + 关键配方文档化",
                        "cost": "100-200万元/年",
                        "rationale": "CEO单一依赖是整个模式最脆弱的一环。须建立制度化的继任机制。",
                    },
                ],
            },
        }

    def generate_financial_response(self, signals: Dict) -> Dict:
        """财务风险对冲方案"""
        quant = signals.get("quantitative", {})
        el_data = quant.get("EL", {})
        var_data = quant.get("VaR", {})
        stress = quant.get("stress_test", {})

        el_value = el_data.get("EL", 0)
        var_value = var_data.get("VaR", 0)
        stress_change = stress.get("change_percent", 0)

        playbook = self._financial_playbook()

        # 根据EL值推荐准备金
        if el_value > 15:
            reserve = "300万元"
        elif el_value > 8:
            reserve = "200万元"
        else:
            reserve = "100万元"

        return {
            "risk_exposure": {
                "expected_loss": f"{el_value:.1f}万元",
                "value_at_risk_95": f"{var_value:.2f}",
                "stress_scenario_worst": f"EL上升{stress_change:.0f}%",
            },
            "loss_reserve": {
                "amount": reserve,
                "explanation": f"基于EL={el_value:.1f}的6个月准备金",
                "funding_source": "营销预算调拨30% + 利润留存",
            },
            "insurance_recommendations": playbook["insurance"],
            "cash_flow_actions": playbook["cash_flow_management"],
        }

    # ============ 辅助方法 ============

    def _collect_all_actions(self, *plans) -> List[Dict]:
        """汇总所有应对方案中的行动项"""
        actions = []
        plan_names = ["供应链", "品牌公关", "法律合规", "市场", "卡脖子", "财务"]

        for plan, name in zip(plans, plan_names):
            # 提取各计划中的关键行动
            if name == "供应链":
                actions.append({
                    "category": name,
                    "action": "启动备选供应商评估",
                    "detail": "优先联系Siam Coconut Co.和Philippine Coconut Authority",
                    "urgency": 9,
                    "impact": 8,
                    "timeline": "7天内",
                    "cost_estimate": "5万元（供应商审核+样品测试）",
                })
                actions.append({
                    "category": name,
                    "action": "安全库存提升至60天",
                    "detail": "分2批补货，30天内完成",
                    "urgency": 8,
                    "impact": 7,
                    "timeline": "30天内",
                    "cost_estimate": "15万/月（仓储+资金占用）",
                })

            elif name == "品牌公关":
                actions.append({
                    "category": name,
                    "action": "发布官方声明 + CEO回应",
                    "detail": "24小时内在微博/公众号/天猫发布声明",
                    "urgency": 10,
                    "impact": 9,
                    "timeline": "24小时内",
                    "cost_estimate": "3万元（声明撰写+媒体沟通）",
                })
                actions.append({
                    "category": name,
                    "action": "委托SGS进行全批次检测",
                    "detail": "公布检测结果以重建消费者信任",
                    "urgency": 9,
                    "impact": 8,
                    "timeline": "3天内送检",
                    "cost_estimate": "8万元（检测费）",
                })

            elif name == "法律合规":
                actions.append({
                    "category": name,
                    "action": "食品标签全面审查整改",
                    "detail": "营养成分表重新检测并更新标签",
                    "urgency": 9,
                    "impact": 7,
                    "timeline": "2周内",
                    "cost_estimate": "5万元",
                })
                actions.append({
                    "category": name,
                    "action": "产品责任纠纷诉讼和解评估",
                    "detail": "评估主动和解vs应诉的成本和风险",
                    "urgency": 7,
                    "impact": 6,
                    "timeline": "1周内完成评估",
                    "cost_estimate": "3-5万元（和解金）",
                })

            elif name == "市场":
                actions.append({
                    "category": name,
                    "action": "天猫旗舰店'品质溯源'专区上线",
                    "detail": "展示泰国产地实拍+SGS报告",
                    "urgency": 8,
                    "impact": 7,
                    "timeline": "1周内",
                    "cost_estimate": "2万元（页面开发）",
                })

            elif name == "卡脖子":
                actions.append({
                    "category": name,
                    "action": "采购去依赖化（新增3家采集商）",
                    "detail": "6个月内将General Beverage采购占比从100%降至70%，新增泰国本地采集商",
                    "urgency": 10,
                    "impact": 9,
                    "timeline": "6个月内",
                    "cost_estimate": "200-500万元（供应商开发+资质审查+合同签订）",
                })
                actions.append({
                    "category": name,
                    "action": "原料产地多元化（测试印尼/菲律宾椰子）",
                    "detail": "12个月内建立印尼和菲律宾椰子水小规模测试采购线",
                    "urgency": 8,
                    "impact": 8,
                    "timeline": "12个月内",
                    "cost_estimate": "100-300万元（样品测试+小规模试产+消费者口感盲测）",
                })
                actions.append({
                    "category": name,
                    "action": "CEO继任计划+研发团队扩编",
                    "detail": "建立CEO突发情况应急预案，研发团队从5人扩至10人，关键配方文档化",
                    "urgency": 7,
                    "impact": 9,
                    "timeline": "3个月内启动",
                    "cost_estimate": "100-200万元/年",
                })
                actions.append({
                    "category": name,
                    "action": "代工厂产能分散化",
                    "detail": "将前5大代工厂产能占比从96.9%降至80%以下，新增2-3家备选代工厂",
                    "urgency": 6,
                    "impact": 7,
                    "timeline": "12-18个月",
                    "cost_estimate": "300-800万元",
                })

            elif name == "财务":
                actions.append({
                    "category": name,
                    "action": "建立风险准备金",
                    "detail": "从营销预算调拨30%，设立200万准备金",
                    "urgency": 7,
                    "impact": 8,
                    "timeline": "1个月内",
                    "cost_estimate": "200万元（准备金，非费用）",
                })
                actions.append({
                    "category": name,
                    "action": "投保产品召回险",
                    "detail": "500万元保额，年费8-12万",
                    "urgency": 6,
                    "impact": 7,
                    "timeline": "2周内完成投保",
                    "cost_estimate": "8-12万/年",
                })

        return actions

    def _prioritize_actions(self, actions: List[Dict], crisis_level: Dict) -> List[Dict]:
        """按紧急度×影响力排序"""
        for action in actions:
            action["priority_score"] = action["urgency"] * action["impact"]
            # 危机等级加权
            if crisis_level["level"] == "red":
                action["priority_score"] *= 1.5
            elif crisis_level["level"] == "orange":
                action["priority_score"] *= 1.2

        return sorted(actions, key=lambda x: x["priority_score"], reverse=True)

    def _estimate_total_cost(self, actions: List[Dict]) -> Dict:
        """估算总成本"""
        total = 0
        cost_items = []
        for action in actions:
            cost_str = action.get("cost_estimate", "0元")
            # 简单提取数字
            import re
            numbers = re.findall(r'[\d.]+', cost_str)
            if numbers:
                cost_items.append({
                    "action": action["action"],
                    "estimate": cost_str,
                })

        return {
            "immediate_costs": "约45-55万元（声明+检测+标签整改+供应商评估）",
            "short_term_costs": "约230-260万元（准备金+库存增加+保险+诉讼）",
            "total_estimated_range": "275-315万元",
            "breakdown": cost_items[:8],
        }

    def _generate_timeline(self, actions: List[Dict], crisis_level: Dict) -> List[Dict]:
        """生成执行时间线"""
        now = datetime.now()

        timeline = [
            {
                "phase": "紧急响应（0-48小时）",
                "deadline": (now + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M"),
                "actions": [
                    {"action": "发布官方声明 + CEO回应", "owner": "公关部/CEO办公室"},
                    {"action": "内部调查启动 + SGS送检", "owner": "品控部"},
                    {"action": "统一客服话术 + 社交媒体监控", "owner": "客服部/市场部"},
                ],
            },
            {
                "phase": "短期整改（1-2周）",
                "deadline": (now + timedelta(weeks=2)).strftime("%Y-%m-%d"),
                "actions": [
                    {"action": "食品标签全面审查整改", "owner": "合规部"},
                    {"action": "天猫'品质溯源'专区上线", "owner": "电商部"},
                    {"action": "备选供应商评估 + 样品测试", "owner": "供应链部"},
                    {"action": "产品召回险投保", "owner": "财务部"},
                ],
            },
            {
                "phase": "中期巩固（1-3月）",
                "deadline": (now + timedelta(weeks=12)).strftime("%Y-%m-%d"),
                "actions": [
                    {"action": "安全库存提升至60天", "owner": "供应链部"},
                    {"action": "供应商合同条款重新谈判", "owner": "法务/采购部"},
                    {"action": "品牌信任重建营销战役", "owner": "市场部"},
                    {"action": "建立季度合规审计机制", "owner": "合规部"},
                ],
            },
        ]
        return timeline

    def _generate_executive_summary(self, level: Dict, actions: List[Dict], cost: Dict) -> str:
        """生成执行摘要"""
        top3 = actions[:3]
        summary_parts = [
            f"危机等级：{level['level'].upper()}",
            f"综合评分：{level['score']}/100",
            "",
            "TOP3 优先行动：",
        ]
        for i, action in enumerate(top3, 1):
            summary_parts.append(
                f"  {i}. [{action['category']}] {action['action']} "
                f"(紧急度:{action['urgency']}, 影响:{action['impact']})"
            )
        summary_parts.append(f"\n预计总成本：{cost['total_estimated_range']}")
        return "\n".join(summary_parts)

    def _generate_statement_headline(self, strategy: str) -> str:
        """生成声明标题"""
        headlines = {
            "acknowledge": "【致歉声明】关于IF椰子水产品质量问题的说明与承诺",
            "clarify": "【官方声明】IF椰子水：事实不容歪曲，品质经得起检验",
            "commit": "【品质承诺】IF椰子水全面升级质量管控体系",
            "deflect": "【行业倡议】IF椰子水呼吁建立椰子水行业质量标准",
        }
        return headlines.get(strategy, "")


# ============ 全局实例 ============
response_engine = RiskResponseEngine()


if __name__ == "__main__":
    # 模拟测试
    test_signals = {
        "risk_analysis": {"average_risk_score": 72, "risk_type_summary": {"供应链风险": {"count": 3}}},
        "quantitative": {"EL": {"EL": 18.67}, "VaR": {"VaR": 0.47}, "stress_test": {"change_percent": 50}},
        "ecommerce": {"overview": {"platforms": {"tmall": {"avg_rating": 4.5, "sales_change_pct": -15.8, "negative_review_ratio": 0.11}, "social": {"weibo": {"sentiment_ratio": {"negative": 0.55}}}}}},
        "enterprise": {"risk_score": {"total_score": 59}, "supplier_risks": {"raw_coconut_supply": {"risks": [{"type": "干旱", "probability": 0.65}, {"type": "劳工", "probability": 0.70}]}}},
    }

    engine = RiskResponseEngine()
    plan = engine.generate_full_response_plan(test_signals)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
