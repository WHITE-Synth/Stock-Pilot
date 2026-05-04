from sqlmodel import SQLModel, Field, create_engine, Session, Relationship
from typing import Optional, List
import os

# PostgreSQL database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# PostgreSQL 연결
engine = create_engine(DATABASE_URL, echo=True)

# 사용자 테이블
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    name: str
    
    # 투자성향
    risk_tolerance: Optional[str] = None  # low, medium, high
    investment_goal: Optional[str] = None  # growth, income, balanced
    investment_period: Optional[str] = None  # short, mid, long
    
    portfolios: List["Portfolio"] = Relationship(back_populates="user")

# 포트폴리오 테이블
class Portfolio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = None
    
    user: Optional[User] = Relationship(back_populates="portfolios")
    assets: List["Asset"] = Relationship(back_populates="portfolio")

# 종목 테이블
class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    ticker: str        # 종목 코드 (AAPL, BTC 등)
    name: str          # 종목명
    market: str        # KRX, NYSE, CRYPTO, ETF
    weight: float      # 비중 (%)
    
    portfolio: Optional[Portfolio] = Relationship(back_populates="assets")

# 데이터베이스 및 테이블 생성
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 데이터베이스 세션
def get_db():
    with Session(engine) as session:
        yield session