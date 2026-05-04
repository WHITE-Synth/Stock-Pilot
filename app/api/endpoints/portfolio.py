from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
from database.db import get_db, Portfolio, Asset, User
from api.endpoints.auth import get_current_user
import httpx
import os

router = APIRouter()

# 요청 스키마
class AssetInput(BaseModel):
    ticker: str
    name: str
    market: str  # KRX, NYSE, CRYPTO, ETF
    weight: float

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assets: List[AssetInput]

class InvestmentProfile(BaseModel):
    risk_tolerance: str       # low, medium, high
    investment_goal: str      # growth, income, balanced
    investment_period: str    # short, mid, long

# 투자성향 저장
@router.post("/profile")
def save_investment_profile(
    profile: InvestmentProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.risk_tolerance = profile.risk_tolerance
    current_user.investment_goal = profile.investment_goal
    current_user.investment_period = profile.investment_period
    db.add(current_user)
    db.commit()
    return {"message": "투자성향 저장 완료"}

# AI 포트폴리오 추천
@router.post("/recommend")
async def recommend_portfolio(
    profile: InvestmentProfile,
    current_user: User = Depends(get_current_user)
):
    prompt = f"""
    사용자의 투자성향을 바탕으로 포트폴리오를 추천해줘.
    
    - 위험 허용도: {profile.risk_tolerance} (low/medium/high)
    - 투자 목표: {profile.investment_goal} (growth/income/balanced)
    - 투자 기간: {profile.investment_period} (short/mid/long)
    
    다음 형식으로 JSON만 반환해줘 (다른 텍스트 없이):
    {{
        "portfolio_name": "포트폴리오 이름",
        "description": "포트폴리오 설명",
        "assets": [
            {{"ticker": "종목코드", "name": "종목명", "market": "NYSE/KRX/CRYPTO/ETF", "weight": 비중(숫자)}}
        ]
    }}
    """
    
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = res.json()
        import json
        result = json.loads(data["content"][0]["text"])
        return result

# 포트폴리오 저장
@router.post("/save")
def save_portfolio(
    portfolio_data: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = Portfolio(
        user_id=current_user.id,
        name=portfolio_data.name,
        description=portfolio_data.description
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    for asset_data in portfolio_data.assets:
        asset = Asset(
            portfolio_id=portfolio.id,
            ticker=asset_data.ticker,
            name=asset_data.name,
            market=asset_data.market,
            weight=asset_data.weight
        )
        db.add(asset)
    db.commit()
    return {"message": "포트폴리오 저장 완료", "portfolio_id": portfolio.id}

# 포트폴리오 조회
@router.get("/list")
def get_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolios = db.exec(select(Portfolio).where(Portfolio.user_id == current_user.id)).all()
    result = []
    for p in portfolios:
        assets = db.exec(select(Asset).where(Asset.portfolio_id == p.id)).all()
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "assets": [{"ticker": a.ticker, "name": a.name, "market": a.market, "weight": a.weight} for a in assets]
        })
    return result

# 포트폴리오 삭제
@router.delete("/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.get(Portfolio, portfolio_id)
    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")
    db.delete(portfolio)
    db.commit()
    return {"message": "포트폴리오 삭제 완료"}