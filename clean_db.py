# clean_db.py

import os
from sqlalchemy import create_engine
from src.database.models import Base
from config import DATABASE_URL

# 創建資料庫引擎
engine = create_engine(DATABASE_URL)


def clean_and_reset_db():
    """
    清空所有表格並重新建立資料庫結構。
    """
    try:
        print("--- 開始清空資料庫 ---")

        # 1. 銷毀所有表格 (DROP ALL TABLES)
        Base.metadata.drop_all(bind=engine)
        print("舊有的 'products' 和 'price_records' 表格已成功刪除。")

        # 2. 重新創建表格 (CREATE ALL TABLES)
        Base.metadata.create_all(bind=engine)
        print("資料庫結構已重新建立，數據庫現已清空。")

        # 額外：刪除 sqlite 檔案 (可選)
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            print(f"提示：SQLite 檔案位於 {db_path}")

    except Exception as e:
        print(f"清空資料庫時發生錯誤: {e}")


if __name__ == '__main__':
    # 確認您在 (ruten_price) 環境中執行
    clean_and_reset_db()