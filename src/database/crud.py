# src/database/crud.py

from sqlalchemy.orm import Session
from .models import Product, PriceRecord


def create_or_update_product(db: Session, ruten_id: str, name: str, url: str, search_term: str) -> Product:
    """
    如果商品不存在則創建，並在 Session 中刷新以獲取 ID；否則返回現有商品。
    """
    product = db.query(Product).filter(Product.ruten_id == ruten_id).first()

    if not product:
        product = Product(
            ruten_id=ruten_id,
            name=name,
            url=url,
            search_term=search_term
        )
        db.add(product)

        # <<< 關鍵修正：執行 db.flush() 以強制將新紀錄寫入資料庫，
        #             並讓 product 物件獲得自動生成的 primary key (id)。 >>>
        db.flush()

    return product


def add_price_record(db: Session, product_id: int, price: float):
    """為指定商品添加新的價格紀錄。"""
    # 此處 product_id 來自上方 product.id，現在保證是非 None 的
    price_record = PriceRecord(
        product_id=product_id,
        price=price
    )
    db.add(price_record)


def get_all_tracking_products(db: Session):
    """獲取所有正在追蹤的商品。"""
    return db.query(Product).filter(Product.is_tracking == 1).all()


def get_product_price_history(db: Session, product_id: int):
    """獲取某個商品的歷史價格紀錄。"""
    return db.query(PriceRecord).filter(PriceRecord.product_id == product_id).order_by(
        PriceRecord.crawl_timestamp).all()