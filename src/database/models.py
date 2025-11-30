# src/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    ruten_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    search_term = Column(String)
    is_tracking = Column(Integer, default=1)
    prices = relationship("PriceRecord", back_populates="product", cascade="all, delete-orphan")

class PriceRecord(Base):
    __tablename__ = 'price_records'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price = Column(Float, nullable=False)
    crawl_timestamp = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="prices")