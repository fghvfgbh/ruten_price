# src/database/__init__.py (最終修正)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from config import DATABASE_URL 

# 【關鍵修正：將相對導入改為絕對導入】
from src.database.models import Base 
# ... (engine 定義保持不變) ...
import os # 確保導入 os

# --- 關鍵修正：確保 engine 和 SessionLocal 在頂部定義 ---
# 這樣它們可以被其他模組正確導入

# 創建資料庫引擎
# DATABASE_URL 應該指向 'sqlite:///tmp/ruten_price.db'
engine = create_engine(DATABASE_URL)

# 創建 SessionLocal 類別，用於數據庫連線
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# --------------------------------------------------------


def init_db():
    """初始化資料庫：在 /tmp 中創建表格。"""
    
    # 由於資料庫路徑已指向 /tmp/ruten_price.db，這是 Streamlit Cloud 唯一保證可寫入的區域
    # 我們只需確保表格結構被創建
    Base.metadata.create_all(bind=engine)
    

def get_db() -> Generator[SessionLocal, None, None]:
    """獲取一個數據庫會話 (Session)。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
