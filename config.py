# config.py

# --- 資料庫配置 ---
DATABASE_URL = "sqlite:///./data/ruten_price.db"

# --- 爬蟲配置 ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
SLEEP_TIME_SECONDS = 5

# 初次運行時要追蹤的關鍵字列表
INITIAL_TRACKING_KEYWORDS = [
    "BPRO-JP024 金亮",
    "BPRO-JP041"
]
# 每個關鍵字最多爬取的頁數 (為了快速測試，設為 1)
MAX_PAGES_TO_SCRAPE = 1

# --- 排程配置 ---
SCHEDULE_INTERVAL_HOURS = 6