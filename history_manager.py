"""
history_manager.py - 历史记录管理模块
功能：
1. 保存每次分析的历史记录
2. 查询最近的历史记录
3. 查看单条记录详情
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class HistoryRecord:
    """历史记录数据类"""
    id: str
    timestamp: str
    keyword: str
    total_articles: int
    risky_articles: int
    risk_score: float
    risk_level: str
    sentiment_distribution: Dict
    summary: str
    full_data: Optional[Dict] = None


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, data_dir: str = "history_data"):
        self.data_dir = data_dir
        self._ensure_data_dir()
        self.records_file = os.path.join(data_dir, "records.json")
        self.records = self._load_records()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_records(self) -> List[Dict]:
        """加载历史记录"""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_records(self):
        """保存历史记录"""
        with open(self.records_file, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def add_record(self, keyword: str, analysis_data: Dict) -> str:
        """
        添加新的历史记录

        Args:
            keyword: 分析关键词
            analysis_data: 分析结果数据

        Returns:
            记录ID
        """
        # 生成记录ID（时间戳+序号）
        record_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 提取关键信息
        summary = self._generate_summary(analysis_data)

        record = {
            'id': record_id,
            'timestamp': datetime.now().isoformat(),
            'keyword': keyword,
            'total_articles': analysis_data.get('total_articles', 0),
            'risky_articles': analysis_data.get('risky_articles', 0),
            'risk_score': analysis_data.get('average_risk_score', 0),
            'risk_level': analysis_data.get('overall_risk_level', '未知'),
            'sentiment_distribution': analysis_data.get('sentiment_distribution', {}),
            'summary': summary,
            'has_details': True
        }

        # 保存完整数据到单独文件
        detail_file = os.path.join(self.data_dir, f"detail_{record_id}.json")
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)

        # 添加到记录列表（限制最多50条）
        self.records.insert(0, record)
        if len(self.records) > 50:
            # 删除旧记录的详细数据
            old_record = self.records.pop()
            old_detail_file = os.path.join(self.data_dir, f"detail_{old_record['id']}.json")
            if os.path.exists(old_detail_file):
                try:
                    os.remove(old_detail_file)
                except:
                    pass

        self._save_records()
        return record_id

    def _generate_summary(self, analysis_data: Dict) -> str:
        """生成记录摘要"""
        risk_level = analysis_data.get('overall_risk_level', '未知')
        total = analysis_data.get('total_articles', 0)
        risky = analysis_data.get('risky_articles', 0)

        risk_types = analysis_data.get('risk_type_summary', {})
        if risk_types:
            main_risk = max(risk_types.items(), key=lambda x: x[1]['count'])
            return f"{risk_level}，共发现{total}条信息，其中{risky}条存在风险，主要风险：{main_risk[0]}"

        return f"{risk_level}，共分析{total}条信息"

    def get_recent_records(self, limit: int = 5) -> List[Dict]:
        """
        获取最近的历史记录

        Args:
            limit: 返回条数

        Returns:
            历史记录列表
        """
        return self.records[:limit]

    def get_record_detail(self, record_id: str) -> Optional[Dict]:
        """
        获取单条记录的详细信息

        Args:
            record_id: 记录ID

        Returns:
            完整分析数据，如果不存在返回None
        """
        detail_file = os.path.join(self.data_dir, f"detail_{record_id}.json")
        if os.path.exists(detail_file):
            try:
                with open(detail_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None

    def get_record_summary(self, record_id: str) -> Optional[Dict]:
        """获取记录概要信息"""
        for record in self.records:
            if record['id'] == record_id:
                return record
        return None

    def delete_record(self, record_id: str) -> bool:
        """删除记录"""
        for i, record in enumerate(self.records):
            if record['id'] == record_id:
                self.records.pop(i)
                self._save_records()

                # 删除详细数据文件
                detail_file = os.path.join(self.data_dir, f"detail_{record_id}.json")
                if os.path.exists(detail_file):
                    try:
                        os.remove(detail_file)
                    except:
                        pass
                return True
        return False

    def clear_all_records(self):
        """清空所有历史记录"""
        # 删除所有详细数据文件
        for record in self.records:
            detail_file = os.path.join(self.data_dir, f"detail_{record['id']}.json")
            if os.path.exists(detail_file):
                try:
                    os.remove(detail_file)
                except:
                    pass

        self.records = []
        self._save_records()


# 全局历史记录管理器实例
history_manager = HistoryManager()


# 测试代码
if __name__ == "__main__":
    # 添加测试记录
    test_data = {
        'total_articles': 115,
        'risky_articles': 27,
        'average_risk_score': 62.1,
        'overall_risk_level': '高风险',
        'sentiment_distribution': {'正面': 63, '负面': 45, '中性': 7},
        'risk_type_summary': {
            '供应链风险': {'count': 9},
            '声誉风险': {'count': 6}
        }
    }

    record_id = history_manager.add_record("IF椰子水", test_data)
    print(f"添加记录成功: {record_id}")

    # 查询最近记录
    recent = history_manager.get_recent_records(5)
    print(f"\n最近 {len(recent)} 条记录:")
    for r in recent:
        print(f"  - {r['timestamp']}: {r['summary']}")
