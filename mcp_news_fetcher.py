# -*- coding: utf-8 -*-
"""
MCP Optimized News Fetcher
Integrates with full-data warehouse for intelligent collection strategy
"""

from news_fetcher import NewsFetcher, NewsAggregator
from mcp_data_warehouse import MCPDataWarehouse, MCPFullCollector
from datetime import datetime
from typing import List, Dict
import time


class MCPNewsFetcher:
    """
    MCP Optimized News Fetcher

    Core optimizations:
    1. Local-first: Read from SQLite warehouse, reduce API calls
    2. Incremental collection: Only fetch new data
    3. Full persistence: All data stored, support historical query
    4. Smart cache: Read from DB within 1 hour
    """

    def __init__(self, db_path: str = "./data/risk_sentinel.db"):
        self.warehouse = MCPDataWarehouse(db_path)
        self.base_fetcher = NewsFetcher()
        self.collector = MCPFullCollector(self.warehouse, self.base_fetcher)

    def fetch_news(self, days_back: int = 30, use_cache: bool = True) -> List[Dict]:
        """
        Fetch news (MCP optimized)

        Args:
            days_back: Days to look back
            use_cache: Whether to use local cache

        Returns:
            List of news articles
        """
        print("\n" + "="*60)
        print("MCP Collection Starting")
        print("="*60)

        if use_cache:
            # Strategy 1: Check local data freshness
            cache_stats = self._check_cache_freshness()

            if cache_stats['is_fresh']:
                print(f"[MCP] Local data fresh ({cache_stats['age_minutes']:.0f} mins ago), reading from DB")
                return self._fetch_from_warehouse(days_back)

            print(f"[MCP] Local data stale ({cache_stats['age_minutes']:.0f} mins ago), incremental fetch")

        # Strategy 2: Incremental collection
        collection_results = []

        # Collect from all sources
        sources = ["NewsAPI", "GNews", "RSS-Feeds"]
        for source in sources:
            result = self.collector.collect(source, days_back)
            collection_results.append(result)
            time.sleep(0.5)  # Avoid too fast requests

        # Print collection summary
        print("\n" + "-"*60)
        print("Collection Summary:")
        total_new = sum(r['records_new'] for r in collection_results)
        total_dup = sum(r['records_duplicate'] for r in collection_results)
        print(f"  New records: {total_new}")
        print(f"  Duplicates: {total_dup}")
        print("-"*60)

        # Return complete data from warehouse
        return self._fetch_from_warehouse(days_back)

    def _check_cache_freshness(self) -> Dict:
        """Check cache freshness"""
        # Query last collection time
        last_fetch = None
        for source in ["NewsAPI", "GNews", "RSS-Feeds"]:
            fetch_time = self.warehouse.get_last_fetch_time(source)
            if fetch_time and (last_fetch is None or fetch_time > last_fetch):
                last_fetch = fetch_time

        if last_fetch is None:
            return {'is_fresh': False, 'age_minutes': float('inf')}

        age_minutes = (datetime.now() - last_fetch).total_seconds() / 60

        return {
            'is_fresh': age_minutes < 60,  # Consider fresh within 1 hour
            'age_minutes': age_minutes,
            'last_fetch': last_fetch.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _fetch_from_warehouse(self, days_back: int) -> List[Dict]:
        """Read data from warehouse"""
        from datetime import timedelta

        articles = self.warehouse.query_by_date_range(
            datetime.now() - timedelta(days=days_back),
            datetime.now()
        )

        print(f"[MCP] Read from warehouse: {len(articles)} records")
        return articles

    def get_warehouse_stats(self) -> Dict:
        """Get warehouse statistics"""
        return self.warehouse.get_statistics()

    def export_data(self, filepath: str):
        """Export full dataset"""
        self.warehouse.export_to_json(filepath)


# ==================== Compatible Wrapper ====================

class MCPCompatibleFetcher:
    """
    MCP fetcher compatible with existing interface

    Usage:
    from mcp_news_fetcher import MCPCompatibleFetcher as NewsFetcher
    """

    def __init__(self):
        self.fetcher = MCPNewsFetcher()

    def fetch_news(self, days_back: int = 30) -> List[Dict]:
        """Compatible with existing interface"""
        return self.fetcher.fetch_news(days_back, use_cache=True)


# ==================== Usage Example ====================

if __name__ == "__main__":
    print("="*60)
    print("MCP Optimized News Fetcher Test")
    print("="*60)

    # Initialize MCP fetcher
    fetcher = MCPNewsFetcher()

    # First collection (will fetch from API)
    print("\n[First Collection]")
    articles1 = fetcher.fetch_news(days_back=7)
    print(f"Got {len(articles1)} articles")

    # Show warehouse stats
    stats = fetcher.get_warehouse_stats()
    print("\n[Warehouse Stats]")
    print(f"  Total: {stats['total_records']}")
    print(f"  Processed: {stats['processed_records']}")
    print(f"  Sources: {stats['source_distribution']}")

    # Second collection (will hit cache)
    print("\n[Second Collection (Cache Test)]")
    start = time.time()
    articles2 = fetcher.fetch_news(days_back=7)
    duration = time.time() - start
    print(f"Got {len(articles2)} articles, took {duration:.2f} sec")
