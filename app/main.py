from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from api.endpoints import auth, stock, portfolio
from database.db import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WHITE_Synth",
    description="STOCKPILOT",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# React 정적 파일
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static/build/static")), name="static")

# API 라우터
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(stock.router, prefix="/api/market", tags=["market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# React 앱 서빙 (모든 경로)
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    index = BASE_DIR / "static/build/index.html"
    return FileResponse(str(index))