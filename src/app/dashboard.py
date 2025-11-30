# src/app/dashboard.py (雲端部署最終版)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import logging
from sqlalchemy import create_engine 

# 確保導入路徑正確
from src.database.__init__ import get_db, init_db, engine 
from src.database.crud import create_or_update_product, add_price_record
from src.scraper.core import setup_driver, scrape_search_page 
from config import INITIAL_TRACKING_KEYWORDS, MAX_PAGES_TO_SCRAPE 
# --------------------------------------------------------

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 雲端手動啟動爬蟲函式 ---
def run_scraper_manually():
    """在 Streamlit Cloud 環境中手動啟動爬蟲任務。"""
    
    with st.status("正在運行爬蟲...", expanded=True) as status:
        
        init_db() # 確保資料庫結構存在
        
        driver = None
        db = None
        total_items_scraped = 0
        
        try:
            status.update(label="1/3 正在啟動 WebDriver (Chrome)", state="running", expanded=True)
            driver = setup_driver()
            if not driver:
                status.update(label="WebDriver 啟動失敗！請檢查 Cloud 日誌。", state="error")
                return

            db_generator = get_db()
            db = next(db_generator)
            
            # 2. 迭代所有關鍵字並爬取數據
            for term in INITIAL_TRACKING_KEYWORDS:
                for page in range(1, MAX_PAGES_TO_SCRAPE + 1):
                    status.update(label=f"2/3 正在爬取關鍵字: {term} (頁碼: {page})...", state="running")
                    scraped_items = scrape_search_page(driver, term, page=page)
                    
                    if not scraped_items and page > 1: break
                    
                    for item in scraped_items:
                        product = create_or_update_product(db, **item)
                        if product:
                            add_price_record(db, product.id, item['price'])
                            total_items_scraped += 1
            
            # 3. 提交並完成
            db.commit()
            status.update(label=f"✅ 數據更新完成！共計新增 {total_items_scraped} 條價格記錄。", state="complete")
            
        except Exception as e:
            if db: db.rollback()
            status.update(label=f"❌ 爬蟲任務執行期間發生錯誤：{e}", state="error")
            logging.error(f"Cloud Scraper Error: {e}")
        finally:
            if driver: driver.quit()
            st.cache_data.clear() 
            st.rerun() 

# --- (其餘數據載入和圖表函式保持不變) ---
# ...
# --- Streamlit 應用主體 ---
def main():
    st.set_page_config(layout="wide", page_title="露天價格追蹤儀表板")
    st.title("💰 露天拍賣價格趨勢追蹤儀表板")
    st.markdown("---")

    init_db()
    
    # 爬蟲啟動按鈕
    if st.button("手動更新數據 (運行爬蟲)"):
        run_scraper_manually()

    st.markdown("---")
    
    # ... (Tab 1 和 Tab 2 邏輯保持不變) ...

if __name__ == '__main__':
    main()
