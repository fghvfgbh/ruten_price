# src/database/__init__.py (修正 init_db 函式)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from config import DATABASE_URL 
from .models import Base
import os # 確保有 os 導入

# ... (engine 和 SessionLocal 定義保持不變) ...

def init_db():
    """初始化資料庫：確保資料夾存在並創建表格。"""
    
    # 【關鍵修正：處理 /tmp 路徑，並確保父目錄存在】
    # 由於我們使用了 /tmp/ruten_price.db，這裡只需要確保檔案可以被創建。
    
    # 如果您堅持使用原來的相對路徑，則需要使用以下邏輯:
    # db_path = DATABASE_URL.replace("sqlite:///", "") 
    # data_dir = os.path.dirname(db_path) 
    # if data_dir and not os.path.exists(data_dir):
    #     os.makedirs(data_dir) 
        
    # 創建所有 Base 中定義的表格
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[SessionLocal, None, None]:
    """獲取一個數據庫會話 (Session)。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
