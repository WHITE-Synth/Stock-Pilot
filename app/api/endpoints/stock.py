from fastapi import APIRouter, HTTPException
import yfinance as yf
import httpx

router = APIRouter()

# 주식 정보 조회 (한국/미국)
@router.get("/stock/{ticker}")
async def get_stock(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1mo")
        
        return {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "change_percent": info.get("52WeekChange"),
            "market_cap": info.get("marketCap"),
            "history": hist["Close"].tail(30).to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {str(e)}")

# 암호화폐 정보 조회 (CoinGecko)
@router.get("/crypto/{coin_id}")
async def get_crypto(coin_id: str):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={"localization": "false", "tickers": "false"}
            )
            data = res.json()
            return {
                "id": coin_id,
                "name": data["name"],
                "price": data["market_data"]["current_price"]["usd"],
                "change_24h": data["market_data"]["price_change_percentage_24h"],
                "market_cap": data["market_data"]["market_cap"]["usd"],
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"코인을 찾을 수 없습니다: {str(e)}")

# 지수 조회 (S&P500, 코스피 등)
@router.get("/index/{ticker}")
async def get_index(ticker: str):
    try:
        index = yf.Ticker(ticker)
        hist = index.history(period="1mo")
        latest = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        change = ((latest - prev) / prev) * 100
        
        return {
            "ticker": ticker,
            "price": round(latest, 2),
            "change_percent": round(change, 2),
            "history": hist["Close"].tail(30).to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"지수를 찾을 수 없습니다: {str(e)}")