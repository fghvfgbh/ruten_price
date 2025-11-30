# src/scraper/core.py (最終 PyInstaller 兼容版)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging
import os
import sys  # 新增導入 sys
from typing import List, Dict, Any

from config import USER_AGENT, SLEEP_TIME_SECONDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def resource_path(relative_path):
    """獲取資源的絕對路徑，適用於開發和 PyInstaller 打包環境"""
    try:
        # PyInstaller 在打包時會創建一個臨時資料夾 _MEIPASS
        # 這裡假設 drivers/ 資料夾被正確打包
        base_path = sys._MEIPASS
    except Exception:
        # 在開發環境中，計算到專案根目錄
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_file_dir, '..', '..'))

    return os.path.join(base_path, relative_path)


# --- 核心配置：ChromeDriver 路徑 ---
# 使用修正後的函式來獲取路徑
CHROME_DRIVER_PATH = resource_path('drivers/chromedriver.exe')


# ------------------------------------

# src/scraper/core.py (移除所有 Headless 相關參數)

# ... (導入保持不變) ...

def setup_driver():
    """配置並啟動 Selenium WebDriver (最終穩定非 Headless 隱藏模式)。"""
    chrome_options = Options()

    # 【關鍵修正】：移除 --headless 參數，確保穩定運行

    # 保持基本穩定參數
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 設置視窗大小，讓它在背景以隱藏視窗運行 (模擬 Headless 效果)
    chrome_options.add_argument("--window-size=1920,1080")

    # 設置 User-Agent
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument("--ignore-certificate-errors")

    # (其他優化保持不變)

    try:
        # ... (檢查路徑邏輯保持不變) ...

        logging.info("Attempting to start Chrome Driver in stable non-Headless mode.")
        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 移除 window.navigator.webdriver 標誌 (保持這項反偵測優化)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logging.info("WebDriver successfully initialized in stable mode.")
        return driver
    except Exception as e:
        logging.error(f"Failed to start Chrome Driver. Error: {e}")
        return None


# ... (scrape_search_page 函式保持不變) ...


def scrape_search_page(driver: webdriver.Chrome, search_term: str, page: int = 1) -> List[Dict[str, Any]]:
    """
    爬取露天拍賣的搜尋結果頁面，提取商品基本資訊。(包含滾動和 CSS 修正)
    """
    url = f"https://www.ruten.com.tw/find/?q={search_term}&p={page}"
    logging.info(f"-> Starting scrape for: {search_term} (Page {page})")
    items = []

    try:
        driver.get(url)

        # 執行向下滾動和等待，強制延遲加載商品出現
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SLEEP_TIME_SECONDS)

        # 關鍵：等待單個商品項目出現
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.product-item'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 修正：定位單個商品區塊
        for item_tag in soup.select('div.product-item'):
            try:
                # 1. 檢查並跳過廣告
                ad_tag = item_tag.select_one('span.rt-product-card-ad-tag')
                if ad_tag and ad_tag.text.strip() == 'AD':
                    logging.warning(f"Skipping AD item for term: {search_term}.")
                    continue

                    # 2. 名稱和連結 (必須存在)
                name_tag = item_tag.select_one('a.rt-product-card-name-wrap')

                # 3. 價格：定位到價格容器
                price_container = item_tag.select_one('.rt-product-card-price-wrap')

                if not name_tag or not price_container:
                    logging.warning(f"Item tag found, but name or price container missing for {search_term}. Skipping.")
                    continue

                # --- 數據提取 ---
                name = name_tag.text.strip()
                item_url = name_tag['href']

                # 4. 提取價格
                price_span = price_container.select_one('.rt-text-price.text-price-dollar')
                if not price_span:
                    logging.warning(f"Price span not found for item: {name}. Skipping.")
                    continue

                # 價格處理
                price_text = price_span.text.strip().replace('$', '').replace('NT$', '').replace(',', '')
                if '~' in price_text:
                    price = float(price_text.split('~')[0])
                else:
                    price = float(price_text) if price_text.replace('.', '').isdigit() else 0.0

                # 提取露天商品 ID
                ruten_id = item_url.split('?')[-1].split('=')[-1]

                items.append({
                    'ruten_id': ruten_id, 'name': name, 'url': item_url,
                    'price': price, 'search_term': search_term
                })

            except Exception as e:
                logging.warning(f"Critical error during parsing item for {search_term}: {e}. Skipping item.")
                continue

    except Exception as e:
        logging.error(f"Error scraping search page {url}: Timeout or element not found. Error: {e}")

    logging.info(f"-> Scraped {len(items)} items.")
    return items