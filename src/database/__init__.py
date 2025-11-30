# src/database/__init__.py (關鍵修正)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from config import DATABASE_URL

# 【關鍵修正：將相對導入改為絕對導入】
# 雖然 models.py 在同一個資料夾，但打包後必須使用絕對導入避免路徑錯誤
from src.database.models import Base

engine = create_engine(DATABASE_URL)
# ... (其餘程式碼保持不變) ...
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """初始化資料庫：如果表格不存在則創建它們。"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[SessionLocal, None, None]:
    """獲取一個數據庫會話 (Session)。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()