"""
policy_monitor.py - 政策红线预警模块

监控影响IF椰子水的政策/法规/标准变化，参照PDF Module 3框架：
1. 食品安全法规红线（GB标准 + 标签规范 + 添加剂）
2. 进口通关合规（海关注册 + 检验检疫 + 未准入境）
3. 广告/营销合规（不得使用"零添加"等禁用语）
4. 贸易政策（中泰关税 + 原产地规则）
5. 执法动态（市场监管处罚 + 产品召回）

数据来源：
- 国家卫健委: GB 7718-2025, GB 28050-2025, GB 2760-2024
- 海关总署: 280号令(2026-06-01实施) + 未准入境月度通报
- 市场监管总局: 100号令(食品标识监督管理办法)
- 商务部: 中泰自贸协定
- 香港交易所: IFBH公告中的风险提示

分析对象: IF椰子水(泰国进口预包装饮料)
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class PolicyMonitor:
    """政策红线监控器 - IF椰子水适用的法规全景"""

    # ===== 法规数据库（基于公开法规 + 网络调研） =====

    # IF椰子水产品特征
    PRODUCT_PROFILE = {
        "category": "进口预包装饮料（果蔬汁类）",
        "origin": "泰国",
        "import_channels": ["一般贸易", "跨境电商"],
        "key_claims": ["100%纯椰子水", "无添加糖", "泰国原装进口"],
        "target_consumers": "全年龄段（含儿童青少年）",
        "packaging": "铝罐/纸盒/塑料瓶",
        "shelf_life": "12个月",
    }

    # 现行适用法规（截至2026-05）
    CURRENT_REGULATIONS = [
        {
            "id": "REG-001",
            "name": "GB 7718-2011 预包装食品标签通则",
            "type": "标签",
            "status": "现行 → 将被GB 7718-2025替代",
            "deadline": "2027-03-16",
            "risk_impact": "high",
            "requirement": "强制标示内容11项：食品名称、配料表、净含量、进口商信息、原产国、生产日期、保质期、贮存条件等",
            "if_violation_risk": "中英文标签不对应、营养声称不规范——占进口不合格的50%+",
            "estimated_fine": "货值30%以下或标签成本3-5倍",
        },
        {
            "id": "REG-002",
            "name": "GB 28050-2011 预包装食品营养标签通则",
            "type": "标签",
            "status": "现行 → 将被GB 28050-2025替代",
            "deadline": "2027-03-16",
            "risk_impact": "high",
            "requirement": "强制标示1+4（能量+蛋白质+脂肪+碳水化合物+钠）",
            "if_violation_risk": "营养成分表标注值与检测值不符（IF已被海关处罚5.2万元）",
            "estimated_fine": "5-10万元/批次",
        },
        {
            "id": "REG-003",
            "name": "GB 2760-2024 食品添加剂使用标准",
            "type": "添加剂",
            "status": "现行（2025-02-08实施）",
            "deadline": None,
            "risk_impact": "medium",
            "requirement": "椰子水不得添加防腐剂/甜味剂/着色剂",
            "if_violation_risk": "添加糖浆但标注'100%纯椰子水'=虚假宣传（IF正面临此指控）",
            "estimated_fine": "货值5-10倍或5-50万元",
        },
        {
            "id": "REG-004",
            "name": "海关总署280号令 进口食品境外生产企业注册",
            "type": "进口注册",
            "status": "2026-06-01实施（🟡 倒计时中）",
            "deadline": "2026-06-01",
            "risk_impact": "critical",
            "requirement": "新增'清单注册模式'，境外生产企业须在华注册",
            "if_violation_risk": "未注册/注册过期=无法通关，整批退运",
            "estimated_fine": "退运/销毁 + 商业损失",
        },
        {
            "id": "REG-005",
            "name": "市场监管总局100号令 食品标识监督管理办法",
            "type": "标签",
            "status": "2025-03发布 → 2027-03-16实施",
            "deadline": "2027-03-16",
            "risk_impact": "high",
            "requirement": "禁止'零添加''不添加'等用语 + 日期按年月日顺序 + 致敏原强制标示",
            "if_violation_risk": "IF宣称'100%纯椰子水''无添加糖'在新规下可能不合规",
            "estimated_fine": "10-100万元",
        },
        {
            "id": "REG-006",
            "name": "GB 7101-2022 食品安全国家标准 饮料",
            "type": "产品标准",
            "status": "现行",
            "deadline": None,
            "risk_impact": "medium",
            "requirement": "微生物限量、重金属限量、真菌毒素限量",
            "if_violation_risk": "菌落总数超标=强制召回",
            "estimated_fine": "货值5-10倍",
        },
        {
            "id": "REG-007",
            "name": "中国-东盟自贸协定(ACFTA) 原产地规则",
            "type": "贸易",
            "status": "现行（3.0版升级谈判中）",
            "deadline": None,
            "risk_impact": "medium",
            "requirement": "凭Form E原产地证书享受0关税",
            "if_violation_risk": "原产地证不合规→补缴关税+滞纳金",
            "estimated_fine": "关税差额+每日0.05%滞纳金",
        },
        {
            "id": "REG-008",
            "name": "GB/T 31121-2014 果蔬汁类及其饮料",
            "type": "产品标准",
            "status": "现行",
            "deadline": None,
            "risk_impact": "low",
            "requirement": "果蔬汁含量、可溶性固形物等理化指标",
            "if_violation_risk": "理化指标不达标=标签宣称与实际不符",
            "estimated_fine": "警告至5万元",
        },
    ]

    # 即将生效的新法规（须重点跟踪）
    UPCOMING_REGULATIONS = [
        {
            "id": "UPCOMING-001",
            "name": "GB 7718-2025 预包装食品标签通则",
            "effective_date": "2027-03-16",
            "key_changes": [
                "致敏物质由推荐→强制标示（八大致敏原须加粗/下划线）",
                "中外文必须一一对应（含配料表、营养标签）",
                "保质期到期日优先标示",
            ],
            "if_impact": "IF椰子水含坚果（椰子来源），属于致敏原？须确认",
            "action_required": "2026年底前启动标签换版设计",
            "urgency": "high",
        },
        {
            "id": "UPCOMING-002",
            "name": "GB 28050-2025 预包装食品营养标签通则",
            "effective_date": "2027-03-16",
            "key_changes": [
                "强制标示从1+4升级为1+6（新增饱和脂肪+糖）",
                "须标注'儿童青少年应避免过量摄入盐油糖'",
                "禁止'零添加''不添加''无添加''未添加'等用语",
            ],
            "if_impact": "IF宣称'无添加糖'→新规下违规！须修改为'糖含量0g/100mL'",
            "action_required": "立即停止使用'零添加'类宣传语，准备营养标签换版",
            "urgency": "critical",
        },
        {
            "id": "UPCOMING-003",
            "name": "海关总署280号令 进口食品境外生产企业注册",
            "effective_date": "2026-06-01",
            "key_changes": [
                "新增清单注册模式，降低小微境外企业注册门槛",
                "境外生产企业须在华注册，标签须标注注册编号",
            ],
            "if_impact": "泰国加工厂（IF Coconut Processing Thailand）须完成在华注册",
            "action_required": "立即确认泰国工厂的注册状态，补全注册编号",
            "urgency": "critical",
        },
    ]

    # 行业执法案例（基于海关/市监局公开通报的真实数据）
    ENFORCEMENT_CASES = [
        {
            "date": "2026-01-12",
            "authority": "深圳海关",
            "case": "IF椰子水350ml批次中文标签营养成分表标注值与检测值不符",
            "violation": "GB 28050-2011（营养成分标注不实）",
            "penalty": "罚款5.2万元 + 整改后放行",
            "precedent_value": "同类违规的典型处罚标准",
        },
        {
            "date": "2025-09-28",
            "authority": "深圳市市监局",
            "case": "食品经营许可证到期未及时续期",
            "violation": "食品经营许可管理办法",
            "penalty": "罚款1.0万元 + 限期整改",
            "precedent_value": "证照管理疏忽的典型案例",
        },
        {
            "date": "2025年（全年统计）",
            "authority": "海关总署",
            "case": "全国443批次食品未准入境（标签问题占比超50%）",
            "violation": "多法规交叉",
            "penalty": "退运/销毁",
            "precedent_value": "标签合规是进口食品最大风险点",
        },
    ]

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        if not os.path.exists("data"):
            os.makedirs("data")

    def get_full_report(self) -> Dict:
        """获取完整政策风险评估报告"""
        print("[Policy] Analyzing regulatory risk for IF Coconut Water...")

        return {
            "generated_at": datetime.now().isoformat(),
            "product_profile": self.PRODUCT_PROFILE,
            "regulatory_landscape": self._analyze_landscape(),
            "upcoming_deadlines": self._analyze_upcoming(),
            "compliance_gaps": self._detect_compliance_gaps(),
            "enforcement_risk": self._analyze_enforcement(),
            "policy_risk_score": self._calculate_policy_risk_score(),
        }

    def _analyze_landscape(self) -> Dict:
        """分析现行法规全景"""
        by_type = {}
        for reg in self.CURRENT_REGULATIONS:
            reg_type = reg["type"]
            if reg_type not in by_type:
                by_type[reg_type] = {"count": 0, "high_risk": 0, "critical": 0, "items": []}
            by_type[reg_type]["count"] += 1
            if reg["risk_impact"] == "critical":
                by_type[reg_type]["critical"] += 1
            elif reg["risk_impact"] == "high":
                by_type[reg_type]["high_risk"] += 1
            by_type[reg_type]["items"].append(reg["name"])

        return {
            "total_applicable_regulations": len(self.CURRENT_REGULATIONS),
            "by_type": by_type,
            "summary": (
                "IF椰子水作为泰国进口预包装饮料，在中国市场须同时满足8项核心法规。"
                "其中标签类合规（3项标准+1项管理办法）构成最大风险敞口——"
                "海关统计显示标签问题占进口食品不合格批次的50%以上。"
            ),
        }

    def _analyze_upcoming(self) -> List[Dict]:
        """分析即将生效的法规及紧迫度"""
        deadlines = []
        today = datetime.now()

        for reg in self.UPCOMING_REGULATIONS:
            try:
                eff_date = datetime.strptime(reg["effective_date"], "%Y-%m-%d")
                days_remaining = (eff_date - today).days
            except:
                days_remaining = 365

            deadlines.append({
                **reg,
                "days_remaining": days_remaining,
                "urgency_level": (
                    "immediate" if days_remaining < 30 else
                    "urgent" if days_remaining < 180 else
                    "planned" if days_remaining < 365 else
                    "monitor"
                ),
            })

        # 按紧急度排序
        deadlines.sort(key=lambda x: x["days_remaining"])
        return deadlines

    def _detect_compliance_gaps(self) -> List[Dict]:
        """
        检测IF椰子水当前的合规缺口
        基于公开数据和产品特征分析
        """
        gaps = [
            {
                "id": "GAP-001",
                "area": "标签宣称合规",
                "current_status": "产品包装标注'100%纯椰子水'、'无添加糖'",
                "risk": "市场监管总局100号令+GB 28050-2025生效后，'无添加'类用语被明确禁止",
                "severity": "critical",
                "effective_date": "2027-03-16",
                "action": "停止使用'无添加糖'宣称，改为'糖含量0g/100mL'（须有检测报告支撑）",
                "timeline": "建议2026Q3前完成标签改版",
            },
            {
                "id": "GAP-002",
                "area": "营养标签升级",
                "current_status": "营养成分表为1+4格式（能量+蛋白质+脂肪+碳水化合物+钠）",
                "risk": "GB 28050-2025要求升级为1+6（新增饱和脂肪+糖），须重新检测并换版",
                "severity": "high",
                "effective_date": "2027-03-16",
                "action": "委托SGS/华测检测按新标准重新出具营养成分检测报告",
                "timeline": "建议2026Q4前完成检测并启动标签换版",
            },
            {
                "id": "GAP-003",
                "area": "境外生产企业注册",
                "current_status": "泰国工厂（IF Coconut Processing Thailand）注册状态待确认",
                "risk": "海关总署280号令2026-06-01实施，未注册企业产品将无法通关",
                "severity": "critical",
                "effective_date": "2026-06-01",
                "action": "立即向海关总署确认泰国工厂在华注册编号，确保标签上已标注",
                "timeline": "2026-05-25前必须完成",
            },
            {
                "id": "GAP-004",
                "area": "致敏原标示",
                "current_status": "未标注致敏原信息",
                "risk": "GB 7718-2025将致敏原标示从推荐升级为强制（八大致敏原）",
                "severity": "medium",
                "effective_date": "2027-03-16",
                "action": "评估：椰子是否属于'坚果及其制品'致敏原类别？如不需要，应在配料表中明确区别于其他坚果类致敏原",
                "timeline": "2026Q4完成评估并确定标示方案",
            },
            {
                "id": "GAP-005",
                "area": "数字标签合规",
                "current_status": "未使用数字标签（二维码）",
                "risk": "2025年9月新规鼓励使用数字标签，但不得有弹窗广告",
                "severity": "low",
                "effective_date": "已生效（鼓励性）",
                "action": "考虑在产品上增加二维码链接至电子标签（展示致敏原、溯源信息等），增强消费者信任",
                "timeline": "2026H2可选实施",
            },
        ]

        # 按严重度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda x: severity_order.get(x["severity"], 99))
        return gaps

    def _analyze_enforcement(self) -> Dict:
        """分析执法风险"""
        cases = self.ENFORCEMENT_CASES

        total_penalty = 0
        for case in cases:
            penalty_str = case.get("penalty", "")
            # 提取罚款数字
            import re
            numbers = re.findall(r'[\d.]+(?=\s*万)', penalty_str)
            if numbers:
                total_penalty += float(numbers[0])

        return {
            "historical_cases": cases,
            "total_penalty_wan": total_penalty,
            "recurring_violation_type": "标签合规",
            "key_finding": (
                "IF椰子水深圳总代已有2次行政处罚记录（罚款合计6.2万元）。"
                "海关总署2025年统计显示标签问题占进口食品不合格批次的50%+，"
                "是IF椰子水最大的执法风险敞口。"
            ),
            "likely_next_violation": (
                "如果2027年3月前未完成GB 7718-2025/GB 28050-2025的标签换版，"
                "极大概率将面临新一轮行政处罚。预计罚款10-100万元。"
            ),
        }

    def _calculate_policy_risk_score(self) -> Dict:
        """计算综合政策风险评分（0-100）"""
        factors = {}

        # 法规覆盖密度 (权重20%): IF受8项核心法规约束
        reg_count = len(self.CURRENT_REGULATIONS)
        if reg_count > 8:
            factors["regulatory_density"] = {"score": 18, "level": "high"}
        elif reg_count > 5:
            factors["regulatory_density"] = {"score": 12, "level": "medium"}
        else:
            factors["regulatory_density"] = {"score": 5, "level": "low"}

        # 合规缺口 (权重35%): 5个已知缺口，2个critical
        gaps = self._detect_compliance_gaps()
        critical_gaps = sum(1 for g in gaps if g["severity"] == "critical")
        if critical_gaps >= 2:
            factors["compliance_gaps"] = {"score": 35, "level": "critical"}
        elif critical_gaps >= 1:
            factors["compliance_gaps"] = {"score": 25, "level": "high"}
        else:
            factors["compliance_gaps"] = {"score": 10, "level": "medium"}

        # 即将生效法规紧迫度 (权重25%)
        upcoming = self._analyze_upcoming()
        imminent = [d for d in upcoming if d["days_remaining"] < 30]
        if imminent:
            factors["deadline_pressure"] = {"score": 25, "level": "critical"}
        elif any(d["days_remaining"] < 180 for d in upcoming):
            factors["deadline_pressure"] = {"score": 18, "level": "high"}
        else:
            factors["deadline_pressure"] = {"score": 8, "level": "medium"}

        # 执法历史 (权重20%)
        enforcement = self._analyze_enforcement()
        if enforcement["total_penalty_wan"] > 5:
            factors["enforcement_history"] = {"score": 18, "level": "high"}
        elif enforcement["total_penalty_wan"] > 0:
            factors["enforcement_history"] = {"score": 10, "level": "medium"}
        else:
            factors["enforcement_history"] = {"score": 3, "level": "low"}

        total = sum(f["score"] for f in factors.values())
        level = "critical" if total >= 70 else "high" if total >= 50 else "medium" if total >= 30 else "low"

        return {
            "total_score": total,
            "risk_level": level,
            "factors": factors,
        }


class RegulatoryAlertGenerator:
    """法规预警生成器"""

    @staticmethod
    def generate(policy_report: Dict) -> List[Dict]:
        """根据政策报告生成预警"""
        alerts = []

        deadlines = policy_report.get("upcoming_deadlines", [])
        gaps = policy_report.get("compliance_gaps", [])
        score = policy_report.get("policy_risk_score", {})

        # 紧迫截止日预警
        for d in deadlines:
            if d["urgency_level"] == "immediate":
                alerts.append({
                    "type": "deadline_imminent",
                    "severity": "critical",
                    "regulation": d["name"],
                    "days_remaining": d["days_remaining"],
                    "message": f"{d['name']}将于{d['effective_date']}生效，仅剩{d['days_remaining']}天！{d['action_required']}",
                })

        # 合规缺口预警 (critical only)
        for g in gaps:
            if g["severity"] == "critical":
                alerts.append({
                    "type": "compliance_gap",
                    "severity": "critical",
                    "area": g["area"],
                    "deadline": g.get("effective_date", "未知"),
                    "message": f"[{g['area']}] {g['risk']} — {g['action']}",
                })

        # 综合预警
        if score.get("risk_level") == "critical":
            alerts.append({
                "type": "overall_policy_risk",
                "severity": "high",
                "message": (
                    f"IF椰子水面临多项政策红线风险（综合评分{score['total_score']}/100），"
                    f"海关280号令即将在数月内实施，建议立即启动合规审查。"
                ),
            })

        return alerts


# ===== 全局实例 =====
policy_monitor = PolicyMonitor()


if __name__ == "__main__":
    monitor = PolicyMonitor()
    report = monitor.get_full_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\n=== ALERTS ===")
    alerts = RegulatoryAlertGenerator.generate(report)
    for a in alerts:
        print(f"[{a['severity'].upper()}] {a['message'][:100]}")
