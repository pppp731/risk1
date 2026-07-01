# -*- coding: utf-8 -*-
"""
MCP Data Warehouse Module
基于SQLite的全量数据仓库，支持MCP协议
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import threading
import os


@dataclass
class CollectionLog:
    """采集日志"""
    source: str
    start_time: datetime
    end_time: datetime
    records_fetched: int
    records_new: int
    records_duplicate: int
    status: str


class MCPDataWarehouse:
    """
    MCP数据仓库

    功能：
    1. 全量数据持久化存储
    2. 增量采集支持
    3. 数据去重和清洗
    4. 采集日志记录
    """

    def __init__(self, db_path: str = "./data/risk_sentinel.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_db_directory()
        self._init_tables()

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（线程安全）"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        try:
            yield self._local.conn
        except Exception as e:
            self._local.conn.rollback()
            raise e

    def _init_tables(self):
        """初始化数据表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 原始新闻数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_raw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    source_type TEXT,
                    published_at DATETIME,
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sentiment_score REAL,
                    risk_score REAL,
                    risk_level TEXT,
                    content_hash TEXT,
                    is_processed INTEGER DEFAULT 0
                )
            """)

            # 清洗后的新闻数据
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_clean (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_id INTEGER,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    published_at DATETIME,
                    sentiment_score REAL,
                    sentiment_label TEXT,
                    risk_keywords TEXT,
                    risk_score REAL,
                    risk_level TEXT,
                    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (raw_id) REFERENCES news_raw(id)
                )
            """)

            # 风险事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_title TEXT NOT NULL,
                    description TEXT,
                    related_news_ids TEXT,
                    first_detected DATETIME,
                    last_updated DATETIME,
                    severity INTEGER,
                    status TEXT DEFAULT 'active'
                )
            """)

            # 采集日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    records_fetched INTEGER DEFAULT 0,
                    records_new INTEGER DEFAULT 0,
                    records_duplicate INTEGER DEFAULT 0,
                    status TEXT,
                    error_message TEXT
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_raw_source ON news_raw(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_raw_published ON news_raw(published_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_raw_fetched ON news_raw(fetched_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_raw_hash ON news_raw(content_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_raw_processed ON news_raw(is_processed)")

            conn.commit()
            print(f"[MCP DataWarehouse] Database initialized: {self.db_path}")

    # ==================== 数据采集接口 ====================

    def save_news_batch(self, articles: List[Dict], source: str) -> Tuple[int, int]:
        """
        批量保存新闻数据

        Returns:
            (新增数量, 重复数量)
        """
        new_count = 0
        dup_count = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for article in articles:
                # 生成内容哈希用于去重
                content = f"{article.get('title', '')}{article.get('description', '')}"
                content_hash = hashlib.md5(content.encode()).hexdigest()

                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO news_raw
                        (title, description, content, url, source, source_type,
                         published_at, fetched_at, content_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article.get('title', ''),
                        article.get('description', ''),
                        article.get('content', ''),
                        article.get('url', ''),
                        source,
                        article.get('source_type', source),
                        article.get('published_at'),
                        datetime.now().isoformat(),
                        content_hash
                    ))

                    if cursor.rowcount > 0:
                        new_count += 1
                    else:
                        dup_count += 1

                except Exception as e:
                    print(f"[MCP] Failed to save news: {e}")
                    dup_count += 1

            conn.commit()

        return new_count, dup_count

    def get_last_fetch_time(self, source: str) -> Optional[datetime]:
        """获取上次采集时间"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(fetched_at) as last_fetch
                FROM news_raw
                WHERE source = ?
            """, (source,))
            result = cursor.fetchone()

            if result and result['last_fetch']:
                return datetime.fromisoformat(result['last_fetch'])
            return None

    def get_news_for_analysis(self, days: int = 30, limit: Optional[int] = None) -> List[Dict]:
        """
        获取待分析的新闻数据

        Args:
            days: 多少天内的新闻
            limit: 最大返回数量
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            sql = """
                SELECT * FROM news_raw
                WHERE is_processed = 0
                AND published_at > ?
                ORDER BY published_at DESC
            """
            params = [cutoff_date]

            if limit:
                sql += " LIMIT ?"
                params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def mark_as_processed(self, news_ids: List[int]):
        """标记新闻为已处理"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE news_raw SET is_processed = 1 WHERE id = ?",
                [(id,) for id in news_ids]
            )
            conn.commit()

    # ==================== 数据查询接口 ====================

    def query_by_date_range(self, start: datetime, end: datetime,
                           source: Optional[str] = None) -> List[Dict]:
        """按日期范围查询"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if source:
                cursor.execute("""
                    SELECT * FROM news_raw
                    WHERE published_at BETWEEN ? AND ?
                    AND source = ?
                    ORDER BY published_at DESC
                """, (start.isoformat(), end.isoformat(), source))
            else:
                cursor.execute("""
                    SELECT * FROM news_raw
                    WHERE published_at BETWEEN ? AND ?
                    ORDER BY published_at DESC
                """, (start.isoformat(), end.isoformat()))

            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """获取数据统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 总新闻数
            cursor.execute("SELECT COUNT(*) as total FROM news_raw")
            total = cursor.fetchone()['total']

            # 已处理数
            cursor.execute("SELECT COUNT(*) as processed FROM news_raw WHERE is_processed = 1")
            processed = cursor.fetchone()['processed']

            # 数据源分布
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM news_raw
                GROUP BY source
            """)
            sources = {row['source']: row['count'] for row in cursor.fetchall()}

            # 日期范围
            cursor.execute("""
                SELECT MIN(published_at) as earliest, MAX(published_at) as latest
                FROM news_raw
            """)
            date_range = cursor.fetchone()

            return {
                "total_records": total,
                "processed_records": processed,
                "unprocessed_records": total - processed,
                "source_distribution": sources,
                "date_range": {
                    "earliest": date_range['earliest'],
                    "latest": date_range['latest']
                },
                "database_path": self.db_path,
                "database_size_mb": round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0
            }

    # ==================== 采集日志接口 ====================

    def log_collection(self, log: CollectionLog) -> int:
        """记录采集日志"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO collection_log
                (source, start_time, end_time, records_fetched, records_new, records_duplicate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log.source,
                log.start_time.isoformat(),
                log.end_time.isoformat(),
                log.records_fetched,
                log.records_new,
                log.records_duplicate,
                log.status
            ))
            conn.commit()
            return cursor.lastrowid

    def get_collection_logs(self, limit: int = 10) -> List[Dict]:
        """获取采集日志"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM collection_log
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== MCP协议接口 ====================

    def mcp_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        MCP标准查询接口

        Args:
            sql: SQL查询语句
            params: 查询参数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                print(f"[MCP] Query failed: {e}")
                return []

    def mcp_execute(self, sql: str, params: Optional[tuple] = None) -> bool:
        """MCP标准执行接口"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                conn.commit()
                return True
            except Exception as e:
                print(f"[MCP] Execution failed: {e}")
                conn.rollback()
                return False

    def export_to_json(self, filepath: str, query: Optional[str] = None):
        """导出数据到JSON文件"""
        if query is None:
            query = "SELECT * FROM news_raw ORDER BY published_at DESC"

        data = self.mcp_query(query)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[MCP] Data exported to: {filepath}")


# ==================== 全量采集器 ====================

class MCPFullCollector:
    """
    MCP全量数据采集器

    优化策略：
    1. 优先从本地仓库查询（避免重复API调用）
    2. 增量采集（只采集新数据）
    3. 全量数据持久化
    """

    def __init__(self, warehouse: MCPDataWarehouse, news_fetcher):
        self.warehouse = warehouse
        self.news_fetcher = news_fetcher

    def collect(self, source: str, days_back: int = 30, force_full: bool = False) -> Dict:
        """
        执行数据采集

        Args:
            source: 数据源名称
            days_back: 回溯天数
            force_full: 是否强制全量采集（忽略本地数据）

        Returns:
            采集结果统计
        """
        start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"[MCP Full Collection] Source: {source}, Days: {days_back}")
        print(f"{'='*60}")

        # 检查上次采集时间
        last_fetch = self.warehouse.get_last_fetch_time(source)
        if last_fetch and not force_full:
            hours_since_last = (datetime.now() - last_fetch).total_seconds() / 3600
            print(f"[MCP] Last collection: {last_fetch.strftime('%Y-%m-%d %H:%M:%S')} ({hours_since_last:.1f} hours ago)")

            # 如果1小时内采集过，直接使用本地数据
            if hours_since_last < 1:
                print("[MCP] Local data is fresh, skipping API call")
                local_data = self.warehouse.query_by_date_range(
                    datetime.now() - timedelta(days=days_back),
                    datetime.now(),
                    source
                )
                return {
                    "source": source,
                    "strategy": "local_cache",
                    "records_fetched": len(local_data),
                    "records_new": 0,
                    "records_duplicate": 0,
                    "duration_seconds": (datetime.now() - start_time).total_seconds()
                }

        # 执行API采集
        print(f"[MCP] Fetching new data from API...")
        articles = self.news_fetcher.fetch_news(days_back=days_back)

        # 保存到仓库
        new_count, dup_count = self.warehouse.save_news_batch(articles, source)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 记录日志
        log = CollectionLog(
            source=source,
            start_time=start_time,
            end_time=end_time,
            records_fetched=len(articles),
            records_new=new_count,
            records_duplicate=dup_count,
            status="success"
        )
        self.warehouse.log_collection(log)

        result = {
            "source": source,
            "strategy": "api_fetch",
            "records_fetched": len(articles),
            "records_new": new_count,
            "records_duplicate": dup_count,
            "duration_seconds": duration
        }

        print(f"[MCP] Collection complete: {new_count} new, {dup_count} duplicate, took {duration:.2f} sec")
        return result

    def get_full_dataset(self, days: int = 30) -> List[Dict]:
        """获取全量数据集（本地+增量）"""
        # 先尝试增量采集
        self.collect("NewsAPI", days)
        self.collect("GNews", days)

        # 从仓库获取完整数据
        return self.warehouse.query_by_date_range(
            datetime.now() - timedelta(days=days),
            datetime.now()
        )


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Data Warehouse Test")
    print("=" * 60)

    # Initialize warehouse
    warehouse = MCPDataWarehouse()

    # Show statistics
    stats = warehouse.get_statistics()
    print("\nCurrent Warehouse Statistics:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    # Show collection logs
    logs = warehouse.get_collection_logs(5)
    print(f"\nRecent {len(logs)} collection logs:")
    for log in logs:
        print(f"  [{log['source']}] {log['start_time']}: {log['records_new']} new / {log['records_fetched']} total")
