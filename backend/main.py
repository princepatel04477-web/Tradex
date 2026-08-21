import asyncio
import json
import sys
from pathlib import Path

# Load the repo-root .env before any service reads os.environ. The strategy
# engine needs no keys, but the optional LLM second opinion picks its provider
# from whichever API key is present, and that has to be readable at import time.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
except ImportError:  # python-dotenv is optional; real env vars still work.
    pass

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import List, Optional

from app.schemas import strategy as strategy_api

from app.schemas.market import CurrencyPair, Candle, IndicatorSnapshot, CompositeBias, MarketSessionOverview
from app.schemas.trading import (
    OrderRequest, Position, AccountMetrics, ClosedTrade,
    TradeJournalUpdate, PerformanceAnalytics
)
from app.schemas.ai import RAGQueryRequest, RAGQueryResponse, CurrencySentiment, EconomicEvent
from app.schemas.alerts import AlertCreate, AlertItem
from app.schemas.auth import UserRegister, UserLogin, TokenResponse

from app.services.market_service import market_service
from app.services.analysis_service import analysis_service
from app.services.trading_service import trading_service
from app.services.ai_service import ai_service
from app.services.alert_service import alert_service
from app.services.auth_service import auth_service
from app.services.strategy_service import strategy_service

app = FastAPI(
    title="Tradly API",
    description="AI/ML-Powered Forex Market Intelligence & Algorithmic Trading Platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# MARKET DATA ENDPOINTS (FG-1)
# --------------------------

@app.get("/api/v1/market/pairs", response_model=List[CurrencyPair])
def get_currency_pairs():
    return market_service.get_all_pairs()

@app.get("/api/v1/market/pairs/{symbol}", response_model=CurrencyPair)
def get_currency_pair(symbol: str):
    pair = market_service.get_pair(symbol)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    return pair

@app.get("/api/v1/market/candles/{symbol}", response_model=List[Candle])
def get_candles(
    symbol: str,
    timeframe: str = Query("H1", description="M1, M5, M15, M30, H1, H4, D1"),
    limit: int = Query(100, ge=1, le=500)
):
    return market_service.get_candles(symbol, timeframe, limit)

@app.get("/api/v1/market/sessions", response_model=MarketSessionOverview)
def get_market_sessions():
    return market_service.get_market_sessions()

# --------------------------
# TECHNICAL ANALYSIS ENDPOINTS (FG-2)
# --------------------------

@app.get("/api/v1/analysis/indicators/{symbol}", response_model=IndicatorSnapshot)
def get_indicators(symbol: str, timeframe: str = "H1"):
    return analysis_service.compute_indicators(symbol, timeframe)

@app.get("/api/v1/analysis/bias/{symbol}", response_model=CompositeBias)
def get_composite_bias(symbol: str, timeframe: str = "H1"):
    # Retrieve USD sentiment if present
    sentiments = ai_service.get_currency_sentiments()
    usd_sent = next((s.score for s in sentiments if s.currency == "USD"), 0.0)
    return analysis_service.compute_composite_bias(symbol, timeframe, sentiment_score=usd_sent)

# --------------------------
# PAPER TRADING ENDPOINTS (FG-4 & FG-5)
# --------------------------

@app.get("/api/v1/trading/metrics", response_model=AccountMetrics)
def get_account_metrics():
    trading_service.update_positions_and_check_liquidation()
    return trading_service.get_account_metrics()

@app.post("/api/v1/trading/orders", response_model=Position)
def place_order(order: OrderRequest):
    try:
        return trading_service.place_order(order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/trading/positions", response_model=List[Position])
def get_positions():
    trading_service.update_positions_and_check_liquidation()
    return list(trading_service.positions.values())

@app.post("/api/v1/trading/positions/{position_id}/close", response_model=ClosedTrade)
def close_position(position_id: str):
    try:
        return trading_service.close_position(position_id, reason="manual")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/trading/reset", response_model=AccountMetrics)
def reset_account(balance: float = 10000.0):
    trading_service.reset_account(balance)
    return trading_service.get_account_metrics()

@app.get("/api/v1/trading/analytics", response_model=PerformanceAnalytics)
def get_analytics():
    return trading_service.get_analytics()

@app.get("/api/v1/trading/trades", response_model=List[ClosedTrade])
def get_closed_trades():
    return trading_service.closed_trades

# --------------------------
# AI MARKET INTELLIGENCE ENDPOINTS (FG-3)
# --------------------------

@app.post("/api/v1/ai/rag/query", response_model=RAGQueryResponse)
def rag_query(request: RAGQueryRequest):
    return ai_service.process_rag_query(request)

@app.get("/api/v1/ai/sentiment", response_model=List[CurrencySentiment])
def get_sentiments():
    return ai_service.get_currency_sentiments()

@app.get("/api/v1/ai/calendar", response_model=List[EconomicEvent])
def get_calendar():
    return ai_service.get_economic_calendar()

# --------------------------
# ALERTS ENDPOINTS (FG-6)
# --------------------------

@app.post("/api/v1/alerts", response_model=AlertItem)
def create_alert(alert: AlertCreate):
    try:
        return alert_service.create_alert(alert)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/alerts", response_model=List[AlertItem])
def get_alerts():
    return alert_service.get_alerts()

@app.delete("/api/v1/alerts/{alert_id}")
def delete_alert(alert_id: str):
    success = alert_service.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}

# --------------------------
# AUTH ENDPOINTS (FG-6)
# --------------------------

@app.post("/api/v1/auth/register", response_model=TokenResponse)
def register(user: UserRegister):
    try:
        return auth_service.register(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(user: UserLogin):
    try:
        return auth_service.login(user)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

# --------------------------
# FOREX TOP-DOWN CONFLUENCE TOOLKIT
# Modules 1-14 of the price-action strategy engine (app/strategy).
# --------------------------

# -- Sample data & charting ---------------------------------------------

@app.get("/api/v1/strategy/scenarios", response_model=List[strategy_api.ScenarioOut],
         tags=["strategy"])
def list_scenarios():
    """Bundled OHLC datasets, each demonstrating specific engine behaviour."""
    return strategy_service.scenarios()


@app.get("/api/v1/strategy/candles/{scenario}/{timeframe}",
         response_model=strategy_api.CandleSeries, tags=["strategy"])
def strategy_candles(scenario: str, timeframe: str, limit: int = Query(300, ge=10, le=2000)):
    """OHLC for the candlestick / line chart."""
    try:
        return strategy_service.candle_series(scenario, timeframe, limit)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/strategy/candles/{scenario}/{timeframe}/csv",
         response_class=PlainTextResponse, tags=["strategy"])
def strategy_candles_csv(scenario: str, timeframe: str):
    """Export a series as CSV - the same shape the importer accepts."""
    try:
        return strategy_service.candles_csv(scenario, timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


# -- The full top-down pass ---------------------------------------------

@app.get("/api/v1/strategy/analysis/{scenario}", response_model=strategy_api.AnalysisOut,
         tags=["strategy"])
def strategy_analysis(
    scenario: str,
    account_size: float = Query(10_000.0, gt=0),
    entry_timeframe: str = Query("1H"),
):
    """Trend -> AOI -> break & retest -> pattern -> confluence -> trade plan."""
    try:
        return strategy_service.analyse_scenario(scenario, account_size, entry_timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/strategy/analyse", response_model=strategy_api.AnalysisOut,
          tags=["strategy"])
def strategy_analyse_uploaded(request: strategy_api.AnalysisRequest):
    """Run the same pass over pasted or uploaded CSV data."""
    try:
        return strategy_service.analyse_uploaded(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -- Individual modules --------------------------------------------------

@app.get("/api/v1/strategy/structure/{scenario}/{timeframe}",
         response_model=strategy_api.StructureOut, tags=["strategy"])
def strategy_structure(scenario: str, timeframe: str):
    """HH/HL/LH/LL, CHoCH events, and the snake-trick backtrace."""
    try:
        return strategy_service.structure_for(scenario, timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/strategy/aoi/{scenario}/{timeframe}",
         response_model=strategy_api.AOIScanOut, tags=["strategy"])
def strategy_aoi(scenario: str, timeframe: str):
    """Area of Interest scan. Weekly and Daily only - 4H returns a refusal."""
    try:
        return strategy_service.aoi_for(scenario, timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/strategy/ema/{scenario}/{timeframe}",
         response_model=strategy_api.EMAOut, tags=["strategy"])
def strategy_ema(scenario: str, timeframe: str, period: int = Query(50, ge=2, le=400)):
    """EMA overlay. Supplementary confluence only - structure decides the trend."""
    try:
        return strategy_service.ema_for(scenario, timeframe, period)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/strategy/sessions", response_model=strategy_api.SessionClockOut,
         tags=["strategy"])
def strategy_sessions():
    """Session clock in IST and UTC, with the primary-window flag."""
    return strategy_service.sessions()


# -- Risk ----------------------------------------------------------------

@app.get("/api/v1/strategy/risk/table", response_model=strategy_api.RiskTableOut,
         tags=["strategy"])
def strategy_risk_table():
    """Account-size risk tiers, with the unconfirmed rows flagged."""
    return strategy_service.risk_table()


@app.post("/api/v1/strategy/risk/plan", response_model=strategy_api.TradePlanOut,
          tags=["strategy"])
def strategy_trade_plan(request: strategy_api.TradePlanRequest):
    """Size a trade and validate its reward:risk against the 1:2 floor."""
    try:
        return strategy_service.trade_plan(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -- Reference -----------------------------------------------------------

@app.get("/api/v1/strategy/reference", response_model=strategy_api.ReferenceOut,
         tags=["strategy"])
def strategy_reference():
    """Majors, tools, brokers, golden rules, and every unconfirmed value."""
    return strategy_service.reference()


@app.get("/api/v1/strategy/reference/pairs/{symbol}",
         response_model=strategy_api.PairExplainerOut, tags=["strategy"])
def strategy_pair_explainer(symbol: str, rate: Optional[float] = None):
    """Base/quote breakdown and the buy/sell directional logic for a pair."""
    try:
        return strategy_service.explain_pair(symbol, rate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -- Journal -------------------------------------------------------------

@app.get("/api/v1/strategy/journal", response_model=List[strategy_api.JournalEntryOut],
         tags=["strategy"])
def strategy_journal():
    return strategy_service.journal()


@app.post("/api/v1/strategy/journal", response_model=strategy_api.JournalEntryOut,
          tags=["strategy"])
def strategy_log_trade(request: strategy_api.JournalLogRequest):
    """Log a placed trade with its whole decision trail."""
    return strategy_service.log_trade(request)


@app.post("/api/v1/strategy/journal/{entry_id}/close",
          response_model=strategy_api.JournalEntryOut, tags=["strategy"])
def strategy_close_trade(entry_id: str, request: strategy_api.JournalCloseRequest):
    try:
        return strategy_service.close_trade(entry_id, request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.patch("/api/v1/strategy/journal/{entry_id}/levels",
           response_model=strategy_api.JournalEditResponse, tags=["strategy"])
def strategy_edit_levels(entry_id: str, request: strategy_api.JournalEditRequest):
    """Set & Forget: the edit only applies once the rule is acknowledged."""
    try:
        return strategy_service.edit_levels(entry_id, request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/v1/strategy/journal/{entry_id}", tags=["strategy"])
def strategy_delete_trade(entry_id: str):
    if not strategy_service.delete_trade(entry_id):
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"message": "Journal entry deleted"}


@app.get("/api/v1/strategy/journal/weeks",
         response_model=List[strategy_api.JournalWeekOut], tags=["strategy"])
def strategy_journal_weeks():
    """Trades grouped by ISO week, against the 1-trade-a-week cap."""
    return strategy_service.journal_weeks()


@app.get("/api/v1/strategy/journal/stats", response_model=strategy_api.JournalStatsOut,
         tags=["strategy"])
def strategy_journal_stats():
    return strategy_service.journal_stats()


@app.get("/api/v1/strategy/pace", response_model=strategy_api.WeeklyPaceOut,
         tags=["strategy"])
def strategy_pace():
    """The 1-trade-a-week pacer."""
    return strategy_service.pace()


# -- TradingAgents bridge (optional LLM second opinion) ------------------

@app.get("/api/v1/strategy/review/status", response_model=strategy_api.BridgeStatusOut,
         tags=["strategy"])
def strategy_review_status():
    """Whether the TradingAgents LLM layer is installed and keyed."""
    return strategy_service.bridge_status()


@app.get("/api/v1/strategy/review/{scenario}", response_model=strategy_api.SetupReviewOut,
         tags=["strategy"])
def strategy_review(
    scenario: str,
    account_size: float = Query(10_000.0, gt=0),
    entry_timeframe: str = Query("1H"),
):
    """Bull case / bear case / verdict on a rule-checked setup.

    The engine's verdict is authoritative — the LLM cannot promote a setup the
    rules rejected. Returns ``available: false`` with a reason when no LLM is
    configured; it never fabricates commentary.
    """
    try:
        return strategy_service.review_scenario(scenario, account_size, entry_timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------------
# WEBSOCKET REAL-TIME STREAMING
# --------------------------

@app.websocket("/api/v1/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Simulate real-time tick updates every 1 second
            ticks = market_service.update_ticks()
            trading_service.update_positions_and_check_liquidation()
            
            payload = {
                "type": "ticks_update",
                "timestamp": market_service.get_all_pairs()[0].timestamp.isoformat(),
                "pairs": [p.dict() for p in market_service.get_all_pairs()],
                "metrics": trading_service.get_account_metrics().dict()
            }
            # Convert datetime objects to string
            json_str = json.dumps(payload, default=str)
            await websocket.send_text(json_str)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.get("/")
def read_root():
    return {
        "title": "Tradly API",
        "status": "Online",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
