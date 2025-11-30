# run_schedule.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
import time

# 導入 config 和 src 模組的功能
from config import INITIAL_TRACKING_KEYWORDS, SCHEDULE_INTERVAL_HOURS, MAX_PAGES_TO_SCRAPE
from src.database.__init__ import init_db, get_db
from src.database.crud import create_or_update_product, add_price_record
from src.scraper.core import setup_driver, scrape_search_page

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def tracking_job():
    """
    定時執行的核心任務：爬取數據並存入資料庫。
    """
    logging.info(f"--- [JOB STARTED] Price Tracking at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

    # 1. 初始化資料庫 (確保表格存在)
    init_db()

    # 2. 設置 WebDriver
    driver = setup_driver()
    if not driver:
        logging.error("WebDriver setup failed. Skipping this job run.")
        return

    # 3. 開始數據庫會話
    db_generator = get_db()
    db = next(db_generator)

    try:
        # 4. 迭代所有追蹤關鍵字
        for term in INITIAL_TRACKING_KEYWORDS:

            # 5. 迭代爬取的頁面
            for page in range(1, MAX_PAGES_TO_SCRAPE + 1):
                scraped_items = scrape_search_page(driver, term, page=page)

                # 如果該頁沒有返回商品且不是第一頁，則停止該關鍵字的爬取
                if not scraped_items and page > 1: break

                for item in scraped_items:
                    # 6. 儲存/更新商品資訊 (使用 CRUD 邏輯)
                    product = create_or_update_product(
                        db,
                        ruten_id=item['ruten_id'],
                        name=item['name'],
                        url=item['url'],
                        search_term=item['search_term']
                    )

                    # 7. 儲存價格紀錄 (使用 CRUD 邏輯)
                    if product:
                        add_price_record(db, product.id, item['price'])

        # 8. 統一提交所有變更
        db.commit()
        logging.info("Database commit successful. New price records saved.")

    except Exception as e:
        db.rollback()  # 發生錯誤時回滾
        # <<< 關鍵修正：確保只記錄錯誤 e，不引用未定義的 url 變數 >>>
        logging.critical(f"A critical error occurred. Database transaction rolled back: {e}")

    finally:
        db_generator.close()  # 關閉 Session
        driver.quit()
        logging.info("WebDriver closed.")
        logging.info(f"--- [JOB FINISHED] ---")


def start_scheduler():
    """
    設置和啟動 APScheduler。
    """
    scheduler = BackgroundScheduler()

    # 定義觸發器：每隔 N 小時運行一次 tracking_job
    trigger = IntervalTrigger(hours=SCHEDULE_INTERVAL_HOURS)

    # 添加任務
    scheduler.add_job(
        tracking_job,
        trigger,
        id='ruten_price_tracker_job',
        name='Ruten Price Tracking Job',
        # 第一次運行設為立即啟動
        next_run_time=datetime.now() + timedelta(seconds=1)
    )

    scheduler.start()
    logging.info(f"Scheduler started. Job will run every {SCHEDULE_INTERVAL_HOURS} hours.")
    logging.info("Press Ctrl+C to exit.")

    # 保持主程序運行，等待排程器執行
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler shut down successfully.")


if __name__ == '__main__':
    start_scheduler()