# src/database/__init__.py (修正 init_db 函式)

# src/database/__init__.py (最終修正)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from config import DATABASE_URL 

# 【關鍵修正：從 .models 改為 src.database.models】
from src.database.models import Base 

# ... (engine 定義保持不變) ...
# src/database/__init__.py (修正 init_db 函式)

# ... (確保導入 os)
import os 
# ... (其他導入保持不變)

def init_db():
    """初始化資料庫：在 /tmp 中創建表格。"""
    
    # 由於資料庫路徑已指向 /tmp/ruten_price.db
    # 我們不再需要複雜的 os.makedirs 檢查，直接創建表格
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[SessionLocal, None, None]:
    """獲取一個數據庫會話 (Session)。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
