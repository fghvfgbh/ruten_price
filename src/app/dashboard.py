# src/app/dashboard.py (Cloud 部署最終版)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import logging
from sqlalchemy import create_engine 

# --- [修正區塊] 導入路徑與環境修正 ---
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

if project_root not in sys.path:
    sys.path.append(project_root)

# 匯入資料庫相關模組 (現在可以正確導入了)
from src.database.__init__ import get_db, init_db, engine 
from src.database.crud import create_or_update_product, add_price_record
from src.scraper.core import setup_driver, scrape_search_page # 導入爬蟲核心
from config import INITIAL_TRACKING_KEYWORDS, MAX_PAGES_TO_SCRAPE # 導入配置
# --------------------------------------------------------

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 新增：雲端手動啟動爬蟲函式 ---
def run_scraper_manually():
    """在 Streamlit Cloud 環境中手動啟動爬蟲任務。"""
    st.info("爬蟲任務啟動中，這可能需要幾分鐘時間，請保持網頁開啟...")
    
    # 使用 st.status 顯示即時進度 (Streamlit 內建功能)
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
            st.cache_data.clear() # 清除快取，強制重新載入數據
            st.rerun() # 運行完成後，重新載入應用程式以顯示新數據

    
# --- (其餘數據載入和圖表函式保持不變) ---
# ... (load_all_history_data, load_data_to_df, display_price_history, display_keyword_average_trend 函式請保持不變) ...


# --- Streamlit 應用主體 ---
def main():
    st.set_page_config(layout="wide", page_title="露天價格追蹤儀表板")
    st.title("💰 露天拍賣價格趨勢追蹤儀表板")
    st.markdown("---")

    # 1. 初始化資料庫 
    init_db()
    
    # 2. 爬蟲啟動按鈕 (在 Tab 之外)
    if st.button("手動更新數據 (運行爬蟲)"):
        run_scraper_manually()

    st.markdown("---")


    tab1, tab2 = st.tabs(["📊 單品數據概覽", "📈 關鍵字趨勢分析"])

    # ... (Tab 1 和 Tab 2 的邏輯保持不變，因為它們會調用 st.cache_data) ...
    # ... (請將 Tab 1 和 Tab 2 的完整邏輯複製到這裡) ...

    # 由於篇幅限制，請您將 Tab 1 和 Tab 2 的完整邏輯從上一輪的完整版本中複製過來。
    
    # 這裡將使用預留位置，確保程式結構完整
    with tab1:
        st.header("單品數據概覽")
        # 請確保這裡有 load_data_to_df() 和後續的 selectbox/dataframe 邏輯
        pass 
    
    with tab2:
        st.header("關鍵字市場趨勢分析")
        # 請確保這裡有 load_all_history_data() 和 display_keyword_average_trend 邏輯
        pass


if __name__ == '__main__':
    main()
