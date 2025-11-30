# src/app/dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import logging
from sqlalchemy import create_engine  # 確保導入

# --- [修正區塊] 強制加入專案根目錄到 Python 搜索路徑 ---
# 解決 ModuleNotFoundError: No module named 'src' 的問題
import sys
import os

# 獲取當前檔案所在目錄 (src/app)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 向上退兩級到達專案根目錄 (E:\ruten_price)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# 將專案根目錄加入 sys.path，確保可以找到 src 模組
if project_root not in sys.path:
    sys.path.append(project_root)
# --------------------------------------------------------

# 匯入資料庫相關模組
from src.database.__init__ import get_db, init_db, engine
from src.database.crud import get_all_tracking_products, get_product_price_history

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- 數據載入函式 ---
@st.cache_data
def load_all_history_data():
    """從資料庫讀取所有商品的歷史價格，並返回一個帶有關鍵字的 DataFrame。"""

    query = """
    SELECT 
        p.search_term,
        pr.price,
        pr.crawl_timestamp
    FROM price_records pr
    JOIN products p ON pr.product_id = p.id
    ORDER BY pr.crawl_timestamp;
    """

    try:
        df = pd.read_sql(query, engine)

        if df.empty:
            logging.warning("SQL query returned 0 historical records.")
            return pd.DataFrame()

        # 關鍵修正：將 'crawl_timestamp' 欄位強制轉換為日期時間類型 (解決 .dt 錯誤)
        df['crawl_timestamp'] = pd.to_datetime(df['crawl_timestamp'])

        df['crawl_date'] = df['crawl_timestamp'].dt.normalize()  # 規範到每日
        logging.info(f"Successfully loaded {len(df)} historical records.")

        return df

    except Exception as e:
        logging.error(f"Failed to load all history data (SQL error): {e}")
        st.error(f"資料庫查詢發生錯誤，請檢查 SQL 語法或資料庫連線。錯誤：{e}")
        return pd.DataFrame()


@st.cache_data
def load_data_to_df():
    """從資料庫讀取所有追蹤商品及其最新價格 (用於概覽表格)。"""
    try:
        for db in get_db():
            products = get_all_tracking_products(db)

            data = []
            for p in products:
                history = get_product_price_history(db, p.id)
                latest_price = history[-1] if history else None

                data.append({
                    'ID': p.id,
                    '商品名稱': p.name,
                    '關鍵字': p.search_term,
                    '目前價格': latest_price.price if latest_price else 'N/A',
                    '歷史記錄數': len(history),
                    '最後更新時間': latest_price.crawl_timestamp.strftime('%Y-%m-%d %H:%M') if latest_price else 'N/A',
                    '商品連結': p.url
                })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"無法載入數據庫數據。錯誤: {e}")
        logging.error(f"Database loading error: {e}")
        return pd.DataFrame()


# --- 圖表繪製函式 ---
def display_price_history(product_id: int, product_name: str):
    """展示單個商品的歷史價格趨勢圖。"""
    try:
        for db in get_db():
            history = get_product_price_history(db, product_id)

            if not history:
                st.warning("此商品尚無歷史價格數據。")
                return

            df = pd.DataFrame([{'價格': r.price, '時間': r.crawl_timestamp} for r in history])

            fig = px.line(
                df,
                x='時間',
                y='價格',
                title=f'單一商品價格趨勢: {product_name}',
                labels={'時間': '爬取時間', '價格': '商品價格 (NT$)'}
            )
            fig.update_xaxes(title_text='時間')
            fig.update_yaxes(title_text='價格 (NT$)')
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"繪製圖表時發生錯誤：{e}")
        logging.error(f"Plotting error: {e}")


def display_keyword_average_trend(history_df):
    """計算並繪製關鍵字下的每日平均價格趨勢圖。"""

    df_avg = history_df.groupby(['search_term', 'crawl_date'])['price'].mean().reset_index()
    df_avg.columns = ['關鍵字', '日期', '平均價格']

    if df_avg.empty:
        st.warning("沒有足夠的歷史數據來計算平均趨勢。")
        return

    fig = px.line(
        df_avg,
        x='日期',
        y='平均價格',
        color='關鍵字',
        title='各關鍵字下商品的每日平均價格趨勢',
        labels={'日期': '日期', '平均價格': '平均價格 (NT$)'}
    )
    st.plotly_chart(fig, use_container_width=True)


# --- Streamlit 應用主體 ---
def main():
    st.set_page_config(layout="wide", page_title="露天價格追蹤儀表板")
    st.title("💰 露天拍賣價格趨勢追蹤儀表板")
    st.markdown("---")

    init_db()

    tab1, tab2 = st.tabs(["📊 單品數據概覽", "📈 關鍵字趨勢分析"])

    with tab1:
        st.header("單品數據概覽與詳細歷史")
        product_df = load_data_to_df()

        if not product_df.empty:
            search_terms = ['所有關鍵字'] + sorted(product_df['關鍵字'].unique().tolist())
            selected_term = st.selectbox("請選擇要篩選的關鍵字類別：", search_terms)

            if selected_term == '所有關鍵字':
                filtered_df = product_df.copy()
                display_columns = ['商品名稱', '目前價格', '歷史記錄數', '最後更新時間']
            else:
                filtered_df = product_df[product_df['關鍵字'] == selected_term]
                display_columns = ['商品名稱', '關鍵字', '目前價格', '歷史記錄數', '最後更新時間']

            # 展示數據表
            st.dataframe(
                filtered_df[['ID'] + display_columns].drop(columns=['ID']).reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.subheader(f"詳細商品價格趨勢")

            if not filtered_df.empty:
                product_options = {
                    f"{row['商品名稱']} (ID: {row['ID']})": row['ID']
                    for index, row in filtered_df.iterrows()
                }

                selected_key = st.selectbox(
                    f"請從 '{selected_term}' 類別中選擇一個商品來查看歷史價格：",
                    list(product_options.keys())
                )

                if selected_key:
                    selected_id = product_options[selected_key]
                    selected_name = selected_key.split('(ID:')[0].strip()
                    display_price_history(selected_id, selected_name)
            else:
                st.warning("沒有商品可供繪製趨勢圖。")

        else:
            st.warning("目前資料庫中沒有追蹤的商品數據。")

    with tab2:
        st.header("關鍵字市場趨勢分析")

        full_history_df = load_all_history_data()

        if not full_history_df.empty:

            st.markdown("### 篩選和時間範圍")
            unique_terms = sorted(full_history_df['search_term'].unique().tolist())
            selected_terms = st.multiselect(
                "選擇要比較的主要關鍵字：",
                options=unique_terms,
                default=unique_terms
            )

            filtered_trend_df = full_history_df[full_history_df['search_term'].isin(selected_terms)]

            if not filtered_trend_df.empty:
                display_keyword_average_trend(filtered_trend_df)
            else:
                st.info("請選擇至少一個關鍵字來查看平均價格趨勢。")

        else:
            st.warning("資料庫中無足夠的歷史數據來計算關鍵字平均趨勢。")


if __name__ == '__main__':
    main()