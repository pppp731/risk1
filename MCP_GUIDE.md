# MCP 鍏ㄩ噺鏁版嵁閲囬泦浼樺寲鎸囧崡

## 姒傝堪

鏈枃妗ｄ粙缁嶅浣曚娇鐢  MCP (Model Context Protocol) 瀹炵幇椋庨櫓鍝ㄥ叺绯荤粺鐨勫叏閲忔暟鎹噰闆嗕紭鍖栥€ 

## 鏍稿績鏀硅繘

### 1. 鏁版嵁鎸佷箙鍖 
- **涔嬪墠**: 姣忔鍒嗘瀽閮藉疄鏃惰姹侫PI锛屾棤鏈湴瀛樺偍
- **涔嬪悗**: 鎵€鏈夋暟鎹嚜鍔ㄥ瓨鍏  SQLite 鏁版嵁搴擄紝鏀寔姘镐箙淇濆瓨

### 2. 澧為噺閲囬泦
- **涔嬪墠**: 姣忔閮藉叏閲忚姹傦紝娴垂API閰嶉
- **涔嬪悗**: 鏅鸿兘鍒ゆ柇缂撳瓨鏂伴矞搴︼紝1灏忔椂鍐呮暟鎹洿鎺ヨ搴 

### 3. 鍏ㄩ噺鏌ヨ
- **涔嬪墠**: 浠呮敮鎸佹渶杩 30澶╂暟鎹 
- **涔嬪悗**: 鏀寔浠绘剰鏃堕棿鑼冨洿鐨勫巻鍙叉暟鎹洖婧 

## 鏂囦欢缁撴瀯

```
risk_sentinel/
鈹溾攢鈹€ mcp_config.json          # MCP閰嶇疆鏂囦欢
鈹溾攢鈹€ mcp_data_warehouse.py    # 鏁版嵁浠撳簱妯″潡
鈹溾攢鈹€ mcp_news_fetcher.py      # MCP浼樺寲閲囬泦鍣 
鈹斺攢鈹€ data/
    鈹斺攢鈹€ risk_sentinel.db     # SQLite鏁版嵁搴 
```

## API鎺ュ彛

### 1. 鑾峰彇鏁版嵁浠撳簱缁熻
```http
GET /api/mcp/warehouse/stats
```

**鍝嶅簲绀轰緥:**
```json
{
  "success": true,
  "data": {
    "total_records": 1523,
    "processed_records": 1200,
    "unprocessed_records": 323,
    "source_distribution": {
      "NewsAPI": 420,
      "GNews": 380,
      "RSS-36姘 ": 150
    },
    "date_range": {
      "earliest": "2024-01-15T08:30:00",
      "latest": "2024-04-21T16:45:00"
    },
    "database_size_mb": 2.45
  }
}
```

### 2. 鑾峰彇閲囬泦鏃ュ織
```http
GET /api/mcp/warehouse/logs?limit=10
```

### 3. 鑷畾涔夋煡璇 
```http
POST /api/mcp/warehouse/query
Content-Type: application/json

{
  "sql": "SELECT * FROM news_raw WHERE source = ? ORDER BY published_at DESC LIMIT 10",
  "params": ["NewsAPI"]
}
```

### 4. 瑙﹀彂鍏ㄩ噺閲囬泦
```http
POST /api/mcp/full-collection
Content-Type: application/json

{
  "days_back": 30,
  "force_full": false
}
```

## 閲囬泦绛栫暐璇存槑

### 鏅鸿兘缂撳瓨绛栫暐

```
鐢ㄦ埛璇锋眰鍒嗘瀽
    鈹 
    鈻 
妫€鏌ユ湰鍦版暟鎹柊椴滃害
    鈹 
    鈹溾攢 1灏忔椂鍐呴噰闆嗚繃 鈹€鈹€鈫  鐩存帴璇诲彇SQLite
    鈹 
    鈹斺攢 瓒呰繃1灏忔椂 鈹€鈹€鈹€鈹€鈹€鈫  澧為噺API閲囬泦
                              鈹 
                              鈻 
                        鏂版暟鎹啓鍏QLite
                              鈹 
                              鈻 
                        杩斿洖瀹屾暣鏁版嵁闆 
```

### 鍘婚噸鏈哄埗

1. **URL鍘婚噸**: 鐩稿悓URL鐩存帴璺宠繃
2. **鍝堝笇鍘婚噸**: 鍐呭MD5鍝堝笇姣斿
3. **璇箟鍘婚噸**: 鏍囬鐩镐技搴 >85%瑙嗕负閲嶅

## 鎬ц兘瀵规瘮

| 鎸囨爣 | 浼樺寲鍓  | 浼樺寲鍚  | 鎻愬崌 |
|------|--------|--------|------|
| API璋冪敤娆℃暟 | 姣忔鍒嗘瀽閮借皟鐢  | 1灏忔椂鍙皟1娆  | 90%鈫  |
| 鍝嶅簲鏃堕棿 | 15-30绉  | <1绉 (缂撳瓨鍛戒腑) | 95%鈫  |
| 鏁版嵁鐣欏瓨 | 鏃  | 姘镐箙 | 鈭  |
| 鍘嗗彶鍥炴函 | 30澶  | 鏃犻檺鍒  | 鈭  |

## 浣跨敤绀轰緥

### 绀轰緥1: 鑾峰彇鍏ㄩ噺鏁版嵁

```python
from mcp_news_fetcher import MCPNewsFetcher

fetcher = MCPNewsFetcher()

# 绗竴娆¤皟鐢細浠嶢PI鑾峰彇骞跺瓨鍏ヤ粨搴 
articles = fetcher.fetch_news(days_back=7)
print(f"鑾峰彇 {len(articles)} 鏉℃柊闂 ")

# 绗簩娆¤皟鐢紙1灏忔椂鍐咃級锛氱洿鎺ヨ鍙栦粨搴 
articles = fetcher.fetch_news(days_back=7)
print(f"缂撳瓨鍛戒腑锛岃€楁椂鍑犱箮涓 0")
```

### 绀轰緥2: 鑷畾涔夋煡璇 

```python
from mcp_data_warehouse import MCPDataWarehouse

warehouse = MCPDataWarehouse()

# 鏌ヨ鐗瑰畾鏃ユ湡鑼冨洿
results = warehouse.query_by_date_range(
    start=datetime(2024, 1, 1),
    end=datetime(2024, 3, 31)
)

# MCP鍗忚鏌ヨ
results = warehouse.mcp_query(
    "SELECT * FROM news_raw WHERE risk_level = 'high' ORDER BY published_at DESC"
)
```

### 绀轰緥3: 瀵煎嚭鏁版嵁

```python
# 瀵煎嚭鍏ㄩ噺鏁版嵁涓篔SON
fetcher.export_data("./backup/full_dataset_2024.json")

# 瀵煎嚭鐗瑰畾鏌ヨ缁撴灉
warehouse.export_to_json(
    "./reports/q1_risk_events.json",
    query="SELECT * FROM news_clean WHERE risk_score > 60"
)
```

## 鏁版嵁琛ㄧ粨鏋 

### news_raw (鍘熷鏁版嵁)
| 瀛楁 | 绫诲瀷 | 璇存槑 |
|------|------|------|
| id | INTEGER | 涓婚敭 |
| title | TEXT | 鏍囬 |
| description | TEXT | 鎻忚堪 |
| url | TEXT | 閾炬帴(鍞竴) |
| source | TEXT | 鏁版嵁婧  |
| published_at | DATETIME | 鍙戝竷鏃堕棿 |
| fetched_at | DATETIME | 閲囬泦鏃堕棿 |
| content_hash | TEXT | 鍐呭鍝堝笇 |
| is_processed | INTEGER | 鏄惁宸插鐞  |

### news_clean (娓呮礂鍚庢暟鎹 )
| 瀛楁 | 绫诲瀷 | 璇存槑 |
|------|------|------|
| id | INTEGER | 涓婚敭 |
| raw_id | INTEGER | 鍏宠仈raw琛  |
| sentiment_score | REAL | 鎯呮劅鍒嗘暟 |
| risk_score | REAL | 椋庨櫓鍒嗘暟 |
| risk_level | TEXT | 椋庨櫓绛夌骇 |

### collection_log (閲囬泦鏃ュ織)
| 瀛楁 | 绫诲瀷 | 璇存槑 |
|------|------|------|
| id | INTEGER | 涓婚敭 |
| source | TEXT | 鏁版嵁婧  |
| start_time | DATETIME | 寮€濮嬫椂闂  |
| end_time | DATETIME | 缁撴潫鏃堕棿 |
| records_new | INTEGER | 鏂板鏁伴噺 |
| status | TEXT | 鐘舵€  |

## 鏁呴殰鎺掓煡

### 闂1: 鏁版嵁搴撻攣瀹 
```bash
# 妫€鏌ユ槸鍚︽湁鍏朵粬杩涚▼鍗犵敤
lsof ./data/risk_sentinel.db

# 瑙ｅ喅鏂规锛氶噸鍚湇鍔℃垨绛夊緟浜嬪姟瀹屾垚
```

### 闂2: 鏁版嵁閲嶅
```sql
-- 鏌ユ壘閲嶅URL
SELECT url, COUNT(*) as cnt FROM news_raw
GROUP BY url HAVING cnt > 1;
```

### 闂3: 鎬ц兘涓嬮檷
```bash
# 鏁版嵁搴撲紭鍖 
sqlite3 ./data/risk_sentinel.db "VACUUM;"
```

## 鏈€浣冲疄璺 

1. **瀹氭湡澶囦唤**: 鏁版嵁搴撴枃浠跺畾鏈熷浠藉埌浜戝瓨鍌 
2. **璁剧疆瀹氭椂浠诲姟**: 姣忓皬鏃惰嚜鍔ㄩ噰闆嗕竴娆′繚鎸佹暟鎹柊椴 
3. **鐩戞帶API閰嶉**: 閫氳繃閲囬泦鏃ュ織鐩戞帶API浣跨敤鎯呭喌
4. **鏁版嵁褰掓。**: 瓒呰繃1骞寸殑鏁版嵁鍙綊妗ｅ埌鍐峰瓨鍌 