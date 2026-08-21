"""Forex Strategy Toolkit API router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.schemas import strategy as strategy_api
from app.services.strategy_service import strategy_service

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/scenarios", response_model=List[strategy_api.ScenarioOut])
def list_scenarios():
    return strategy_service.scenarios()


@router.get("/candles/{scenario}/{timeframe}", response_model=strategy_api.CandleSeries)
def strategy_candles(scenario: str, timeframe: str, limit: int = Query(300, ge=10, le=2000)):
    try:
        return strategy_service.candle_series(scenario, timeframe, limit)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/candles/{scenario}/{timeframe}/csv", response_class=PlainTextResponse)
def strategy_candles_csv(scenario: str, timeframe: str):
    try:
        return strategy_service.candles_csv(scenario, timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analysis/{scenario}", response_model=strategy_api.AnalysisOut)
def strategy_analysis(
    scenario: str,
    account_size: float = Query(10_000.0, gt=0),
    entry_timeframe: str = Query("1H"),
):
    try:
        return strategy_service.analyse_scenario(scenario, account_size, entry_timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/analyse", response_model=strategy_api.AnalysisOut)
def strategy_analyse_uploaded(request: strategy_api.AnalysisRequest):
    try:
        return strategy_service.analyse_uploaded(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/structure/{scenario}/{timeframe}", response_model=strategy_api.StructureOut)
def strategy_structure(scenario: str, timeframe: str):
    try:
        return strategy_service.structure_for(scenario, timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/aoi/{scenario}/{timeframe}", response_model=strategy_api.AOIScanOut)
def strategy_aoi(scenario: str, timeframe: str):
    try:
        return strategy_service.aoi_for(scenario, timeframe)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ema/{scenario}/{timeframe}", response_model=strategy_api.EMAOut)
def strategy_ema(scenario: str, timeframe: str, period: int = Query(50, ge=2, le=400)):
    try:
        return strategy_service.ema_for(scenario, timeframe, period)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions", response_model=strategy_api.SessionClockOut)
def strategy_sessions():
    return strategy_service.sessions()


@router.get("/risk/table", response_model=strategy_api.RiskTableOut)
def strategy_risk_table():
    return strategy_service.risk_table()


@router.post("/risk/plan", response_model=strategy_api.TradePlanOut)
def strategy_trade_plan(request: strategy_api.TradePlanRequest):
    try:
        return strategy_service.trade_plan(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reference", response_model=strategy_api.ReferenceOut)
def strategy_reference():
    return strategy_service.reference()


@router.get("/reference/pairs/{symbol}", response_model=strategy_api.PairExplainerOut)
def strategy_pair_explainer(symbol: str, rate: Optional[float] = None):
    try:
        return strategy_service.explain_pair(symbol, rate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/journal", response_model=List[strategy_api.JournalEntryOut])
def strategy_journal():
    return strategy_service.journal()


@router.post("/journal", response_model=strategy_api.JournalEntryOut)
def strategy_log_trade(request: strategy_api.JournalLogRequest):
    return strategy_service.log_trade(request)


@router.post("/journal/{entry_id}/close", response_model=strategy_api.JournalEntryOut)
def strategy_close_trade(entry_id: str, request: strategy_api.JournalCloseRequest):
    try:
        return strategy_service.close_trade(entry_id, request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/journal/{entry_id}/levels", response_model=strategy_api.JournalEditResponse)
def strategy_edit_levels(entry_id: str, request: strategy_api.JournalEditRequest):
    try:
        return strategy_service.edit_levels(entry_id, request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/journal/{entry_id}")
def strategy_delete_trade(entry_id: str):
    if not strategy_service.delete_trade(entry_id):
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"message": "Journal entry deleted"}


@router.get("/journal/weeks", response_model=List[strategy_api.JournalWeekOut])
def strategy_journal_weeks():
    return strategy_service.journal_weeks()


@router.get("/journal/stats", response_model=strategy_api.JournalStatsOut)
def strategy_journal_stats():
    return strategy_service.journal_stats()


@router.get("/pace", response_model=strategy_api.WeeklyPaceOut)
def strategy_pace():
    return strategy_service.pace()


@router.get("/review/status", response_model=strategy_api.BridgeStatusOut)
def strategy_review_status():
    return strategy_service.bridge_status()


@router.get("/review/{scenario}", response_model=strategy_api.SetupReviewOut)
@router.post("/review/setup/{scenario}", response_model=strategy_api.SetupReviewOut)
def strategy_review_setup(
    scenario: str,
    account_size: float = Query(10_000.0, gt=0),
    entry_timeframe: str = Query("1H"),
):
    try:
        return strategy_service.review_scenario(
            scenario, account_size, entry_timeframe
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))
