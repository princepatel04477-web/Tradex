"""HTTP contract for the strategy toolkit routes."""

import pytest
from fastapi.testclient import TestClient

from app.strategy import config
from app.strategy.journal import journal_store
from main import app


@pytest.fixture
def client():
    journal_store.reset()
    yield TestClient(app)
    journal_store.reset()


class TestReferenceRoutes:
    def test_scenarios_are_listed(self, client):
        body = client.get("/api/v1/strategy/scenarios").json()

        assert len(body) >= 3
        assert {s["key"] for s in body} == set(
            __import__("app.strategy.sample_data", fromlist=["SCENARIOS"]).SCENARIOS
        )
        assert all(s["demonstrates"] for s in body)

    def test_reference_carries_the_flagged_questions(self, client):
        body = client.get("/api/v1/strategy/reference").json()

        assert "EUR/USD" in body["majors"]
        assert len(body["golden_rules"]) >= 10
        flagged = {f["id"] for f in body["flagged_for_confirmation"]}
        assert {"sync_rule", "risk_table"} <= flagged

    def test_pair_explainer(self, client):
        body = client.get("/api/v1/strategy/reference/pairs/EUR_USD?rate=1.1").json()

        assert body["base"] == "EUR"
        assert body["quote"] == "USD"
        assert "1 EUR = 1.1 USD" in body["quote_example"]

    def test_unknown_pair_is_a_400(self, client):
        assert client.get("/api/v1/strategy/reference/pairs/NOPE").status_code == 400

    def test_session_clock(self, client):
        body = client.get("/api/v1/strategy/sessions").json()

        assert {s["name"] for s in body["sessions"]} == {
            "Sydney", "Tokyo", "London", "New York"
        }
        assert body["primary_window_ist"].startswith("11:30")
        assert isinstance(body["in_primary_window"], bool)


class TestDataRoutes:
    def test_candles_are_returned_for_charting(self, client):
        body = client.get(
            "/api/v1/strategy/candles/eurusd_bullish_aoi/1D?limit=40"
        ).json()

        assert body["timeframe"] == "1D"
        assert body["count"] == len(body["candles"]) <= 40
        first = body["candles"][0]
        assert first["high"] >= first["low"]

    def test_csv_export_round_trips_into_the_analyser(self, client):
        csv_text = client.get(
            "/api/v1/strategy/candles/eurusd_bullish_aoi/1D/csv"
        ).text
        assert csv_text.startswith("time,open,high,low,close,volume")

        response = client.post(
            "/api/v1/strategy/analyse",
            json={
                "symbol": "EUR_USD",
                "csv_by_timeframe": {"1D": csv_text},
                "entry_timeframe": "1D",
            },
        )
        assert response.status_code == 200
        assert response.json()["top_down"]["trend_layer"]["1D"]["trend"] == "bullish"

    def test_unknown_scenario_is_a_404(self, client):
        assert client.get("/api/v1/strategy/candles/nope/1D").status_code == 404

    def test_upload_without_weekly_or_daily_is_rejected(self, client):
        csv_text = client.get("/api/v1/strategy/candles/eurusd_bullish_aoi/1H/csv").text
        response = client.post(
            "/api/v1/strategy/analyse",
            json={"symbol": "EUR_USD", "csv_by_timeframe": {"1H": csv_text}},
        )

        assert response.status_code == 400
        assert "Weekly or Daily" in response.json()["detail"]

    def test_unparseable_csv_is_a_400(self, client):
        response = client.post(
            "/api/v1/strategy/analyse",
            json={"symbol": "EUR_USD", "csv_by_timeframe": {"1D": "not,a,chart\n1,2,3"}},
        )
        assert response.status_code == 400


class TestModuleRoutes:
    def test_structure_reports_labels_and_the_snake_trace(self, client):
        body = client.get("/api/v1/strategy/structure/eurusd_bullish_aoi/1D").json()

        assert body["trend"] == "bullish"
        assert {s["label"] for s in body["swings"]} & {"HH", "HL"}
        assert body["snake_trace_price"] is not None
        assert body["summary"]

    def test_aoi_on_daily_returns_validated_zones(self, client):
        body = client.get("/api/v1/strategy/aoi/eurusd_bullish_aoi/1D").json()

        assert body["allowed"] is True
        assert body["has_valid_aoi"] is True
        for zone in body["zones"]:
            assert zone["touches"] >= config.AOI.min_touches
            assert 5.0 <= zone["width_pips"] <= 60.0
            assert zone["golden_rule_tag"] in ("Buy zone", "Sell zone")

    def test_aoi_on_4h_is_refused_by_rule(self, client):
        body = client.get("/api/v1/strategy/aoi/eurusd_bullish_aoi/4H").json()

        assert body["allowed"] is False
        assert body["zones"] == []
        assert "never computed on 4H" in body["message"]

    def test_rejected_zones_explain_themselves(self, client):
        body = client.get("/api/v1/strategy/aoi/usdjpy_no_setup/1D").json()

        assert body["has_valid_aoi"] is False
        assert body["rejected"], "near-misses must be reported, not hidden"
        assert all(z["rejection_reasons"] for z in body["rejected"])

    def test_ema_defaults_to_50(self, client):
        body = client.get("/api/v1/strategy/ema/eurusd_bullish_aoi/1D").json()

        assert body["period"] == config.EMA_PERIOD == 50
        assert body["alignment"] in ("bullish", "bearish", "undetermined")


class TestAnalysisRoute:
    def test_full_pass_returns_every_stage(self, client):
        body = client.get("/api/v1/strategy/analysis/eurusd_bullish_aoi").json()

        assert body["bias"] == "bullish"
        assert body["top_down"]["sync"]["in_sync"] is True
        assert body["valid_zones"]
        assert body["trigger"]["is_armed"] is True
        assert body["confluence"]["core_complete"] is True
        assert body["trade_plan"]["direction"] == "buy"
        assert body["session"] is not None
        assert body["narrative"]

    def test_trend_and_entry_layers_stay_separate(self, client):
        body = client.get("/api/v1/strategy/analysis/eurusd_bullish_aoi").json()

        assert set(body["top_down"]["trend_layer"]) == set(config.TREND_TIMEFRAMES)
        assert set(body["top_down"]["entry_layer"]) <= set(config.ENTRY_TIMEFRAMES)

    def test_the_sync_rule_is_reported_as_unconfirmed(self, client):
        body = client.get("/api/v1/strategy/analysis/eurusd_bullish_aoi").json()

        assert body["top_down"]["sync"]["rule_is_unconfirmed"] is True
        assert "UNCONFIRMED" in body["top_down"]["sync"]["rule_note"]

    def test_refusal_is_explicit_not_an_empty_state(self, client):
        body = client.get("/api/v1/strategy/analysis/usdjpy_no_setup").json()

        assert body["tradeable"] is False
        assert body["trade_plan"] is None
        assert config.GUARDRAIL_MESSAGES["no_aoi"] in body["guardrails"]

    def test_head_shoulders_is_surfaced_with_its_neckline(self, client):
        body = client.get("/api/v1/strategy/analysis/gbpusd_head_shoulders").json()

        daily = body["head_shoulders"]["1D"]
        assert daily
        pattern = daily[0]
        assert pattern["neckline_broken"] is True
        assert pattern["is_valid_signal"] is True
        assert pattern["target_price"] is not None

    def test_account_size_changes_the_sizing(self, client):
        small = client.get(
            "/api/v1/strategy/analysis/eurusd_bullish_aoi?account_size=1000"
        ).json()["trade_plan"]
        large = client.get(
            "/api/v1/strategy/analysis/eurusd_bullish_aoi?account_size=100000"
        ).json()["trade_plan"]

        assert large["position_size_lots"] > small["position_size_lots"]
        assert large["entry"] == small["entry"], "levels come from price, not balance"


class TestRiskRoutes:
    def test_risk_table_flags_the_unconfirmed_rows(self, client):
        body = client.get("/api/v1/strategy/risk/table").json()

        assert body["min_reward_risk"] == 2.0
        assert body["target_reward_risk"] == 4.0
        assert body["max_trades_per_week"] == 1
        assert "UNCONFIRMED" in body["note"]

        row = next(t for t in body["tiers"] if t["account_size"] == 17000.0)
        assert row["unconfirmed"] is True

    def test_plan_is_sized_and_validated(self, client):
        body = client.post(
            "/api/v1/strategy/risk/plan",
            json={
                "symbol": "EUR_USD", "direction": "buy",
                "entry": 1.1000, "stop_loss": 1.0950, "account_size": 10000,
            },
        ).json()

        assert body["reward_risk"] == 4.0
        assert body["meets_min_rr"] is True
        assert body["position_size_lots"] > 0
        assert body["stop_distance_pips"] == 50.0

    def test_a_plan_below_the_floor_is_flagged(self, client):
        body = client.post(
            "/api/v1/strategy/risk/plan",
            json={
                "symbol": "EUR_USD", "direction": "buy", "entry": 1.1000,
                "stop_loss": 1.0950, "take_profit": 1.1050, "account_size": 10000,
            },
        ).json()

        assert body["meets_min_rr"] is False
        assert any("below the 1:2 minimum" in w for w in body["warnings"])

    def test_stop_on_the_wrong_side_is_a_400(self, client):
        response = client.post(
            "/api/v1/strategy/risk/plan",
            json={
                "symbol": "EUR_USD", "direction": "buy",
                "entry": 1.1000, "stop_loss": 1.1050, "account_size": 10000,
            },
        )
        assert response.status_code == 400

    def test_invalid_direction_is_rejected_by_validation(self, client):
        response = client.post(
            "/api/v1/strategy/risk/plan",
            json={
                "symbol": "EUR_USD", "direction": "sideways",
                "entry": 1.1, "stop_loss": 1.09, "account_size": 10000,
            },
        )
        assert response.status_code == 422


class TestJournalRoutes:
    TRADE = {
        "symbol": "EUR_USD", "direction": "buy",
        "entry": 1.1000, "stop_loss": 1.0950, "take_profit": 1.1200,
        "position_size_lots": 0.5, "risk_amount": 250.0, "planned_rr": 4.0,
        "sync_state": "Weekly and Daily bullish", "sync_timeframes": ["1W", "1D"],
        "aoi_zone": "1.0940-1.0960", "aoi_timeframe": "1D", "aoi_touches": 4,
        "patterns": ["Bullish Engulfing"], "confluence_score": 8,
        "confluence_max": 10, "low_risk_high_reward": True,
    }

    def test_logging_a_trade_keeps_the_decision_trail(self, client):
        body = client.post("/api/v1/strategy/journal", json=self.TRADE).json()

        assert body["confluence_score"] == 8
        assert body["aoi_touches"] == 4
        assert body["patterns"] == ["Bullish Engulfing"]
        assert body["outcome"] == "open"
        assert body["week_key"].startswith("20")

    def test_a_logged_trade_uses_up_the_weekly_allowance(self, client):
        assert client.get("/api/v1/strategy/pace").json()["at_limit"] is False

        client.post("/api/v1/strategy/journal", json=self.TRADE)
        pace = client.get("/api/v1/strategy/pace").json()

        assert pace["trades_this_week"] == 1
        assert pace["at_limit"] is True
        assert pace["message"] == config.GUARDRAIL_MESSAGES["weekly_pace"]

    def test_closing_a_trade_computes_realised_rr(self, client):
        entry_id = client.post("/api/v1/strategy/journal", json=self.TRADE).json()["id"]

        body = client.post(
            f"/api/v1/strategy/journal/{entry_id}/close",
            json={"exit_price": 1.1200, "pnl": 1000.0},
        ).json()

        assert body["outcome"] == "win"
        assert body["realised_rr"] == pytest.approx(4.0, abs=0.01)

    def test_a_losing_exit_is_classified_as_a_loss(self, client):
        entry_id = client.post("/api/v1/strategy/journal", json=self.TRADE).json()["id"]

        body = client.post(
            f"/api/v1/strategy/journal/{entry_id}/close",
            json={"exit_price": 1.0950},
        ).json()

        assert body["outcome"] == "loss"
        assert body["realised_rr"] == pytest.approx(-1.0, abs=0.01)

    def test_set_and_forget_blocks_a_level_edit_until_acknowledged(self, client):
        entry_id = client.post("/api/v1/strategy/journal", json=self.TRADE).json()["id"]

        blocked = client.patch(
            f"/api/v1/strategy/journal/{entry_id}/levels",
            json={"stop_loss": 1.0900},
        ).json()

        assert blocked["applied"] is False
        assert "Set & Forget" in blocked["notice"]
        assert blocked["entry"]["stop_loss"] == 1.0950, "nothing changed"

        allowed = client.patch(
            f"/api/v1/strategy/journal/{entry_id}/levels",
            json={"stop_loss": 1.0900, "acknowledge_set_and_forget": True},
        ).json()

        assert allowed["applied"] is True
        assert allowed["entry"]["stop_loss"] == 1.0900

    def test_weekly_view_flags_going_over_the_cap(self, client):
        client.post("/api/v1/strategy/journal", json=self.TRADE)
        client.post("/api/v1/strategy/journal", json=self.TRADE)

        weeks = client.get("/api/v1/strategy/journal/weeks").json()
        assert weeks[0]["trade_count"] == 2
        assert weeks[0]["limit"] == 1
        assert weeks[0]["over_limit"] is True

    def test_stats_aggregate_closed_trades(self, client):
        first = client.post("/api/v1/strategy/journal", json=self.TRADE).json()["id"]
        second = client.post("/api/v1/strategy/journal", json=self.TRADE).json()["id"]
        client.post(f"/api/v1/strategy/journal/{first}/close", json={"exit_price": 1.1200})
        client.post(f"/api/v1/strategy/journal/{second}/close", json={"exit_price": 1.0950})

        stats = client.get("/api/v1/strategy/journal/stats").json()
        assert stats["closed_trades"] == 2
        assert stats["wins"] == 1 and stats["losses"] == 1
        assert stats["win_rate"] == 50.0

    def test_deleting_a_trade(self, client):
        entry_id = client.post("/api/v1/strategy/journal", json=self.TRADE).json()["id"]

        assert client.delete(f"/api/v1/strategy/journal/{entry_id}").status_code == 200
        assert client.get("/api/v1/strategy/journal").json() == []

    def test_operating_on_a_missing_trade_is_a_404(self, client):
        assert client.delete("/api/v1/strategy/journal/nope").status_code == 404
        assert client.post(
            "/api/v1/strategy/journal/nope/close", json={"exit_price": 1.1}
        ).status_code == 404


def test_existing_tradly_routes_still_work(client):
    """The toolkit is additive - the original Tradly API must be untouched."""
    assert client.get("/api/v1/market/pairs").status_code == 200
    assert client.get("/api/v1/market/sessions").status_code == 200
    assert client.get("/api/v1/trading/metrics").status_code == 200


class TestTradingAgentsBridge:
    """The LLM layer is optional and must degrade honestly, never invent prose."""

    def test_status_reports_what_is_missing(self, client):
        body = client.get("/api/v1/strategy/review/status").json()

        assert isinstance(body["available"], bool)
        assert body["reason"], "an unavailable bridge must say why"
        if not body["available"]:
            assert "API key" in body["reason"] or "import" in body["reason"]

    def test_review_without_an_llm_returns_no_fabricated_commentary(
        self, client, monkeypatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("TRADINGAGENTS_LLM_PROVIDER", "openai")

        body = client.get("/api/v1/strategy/review/eurusd_bullish_aoi").json()

        assert body["available"] is False
        assert body["reason"]
        # No LLM ran, so there must be no LLM-sounding output at all.
        assert body["bull_case"] == ""
        assert body["bear_case"] == ""
        assert body["verdict"] == ""
        assert body["key_risks"] == []

    def test_the_engine_verdict_is_reported_without_any_llm(self, client):
        """The rule-based verdict needs no API key - it must always be present."""
        body = client.get("/api/v1/strategy/review/eurusd_bullish_aoi").json()

        assert body["symbol"] == "EUR_USD"
        assert "ELIGIBLE" in body["engine_verdict"]

    def test_an_ineligible_setup_is_reported_as_such(self, client):
        body = client.get("/api/v1/strategy/review/usdjpy_no_setup").json()
        assert "NOT ELIGIBLE" in body["engine_verdict"]

    def test_unknown_scenario_is_a_404(self, client):
        assert client.get("/api/v1/strategy/review/nope").status_code == 404


class TestBridgeInternals:
    def test_the_brief_carries_the_facts_the_model_needs(self, client):
        from app.services.strategy_service import strategy_service
        from app.services.tradingagents_bridge import TradingAgentsBridge

        analysis = strategy_service.analyse_scenario("eurusd_bullish_aoi")
        brief = TradingAgentsBridge._build_brief(analysis.model_dump(mode="json"))

        assert "PAIR: EUR_USD" in brief
        assert "ENGINE VERDICT:" in brief
        assert "VALIDATED AOI ZONES:" in brief
        assert "ENTRY TRIGGER:" in brief
        assert "CORE 4:" in brief

    def test_the_refusal_is_carried_into_the_brief(self, client):
        from app.services.strategy_service import strategy_service
        from app.services.tradingagents_bridge import TradingAgentsBridge

        analysis = strategy_service.analyse_scenario("usdjpy_no_setup")
        brief = TradingAgentsBridge._build_brief(analysis.model_dump(mode="json"))

        assert "PLAN: none" in brief
        assert "DISCIPLINE MESSAGES:" in brief

    @pytest.mark.parametrize(
        "raw",
        [
            '{"bull_case": "a", "bear_case": "b", "verdict": "c", "key_risks": ["r"]}',
            '```json\n{"bull_case": "a", "bear_case": "b", "verdict": "c", "key_risks": []}\n```',
            'Here you go:\n{"bull_case": "a", "bear_case": "b", "verdict": "c"}',
        ],
    )
    def test_json_is_recovered_from_common_model_wrappers(self, raw):
        from app.services.tradingagents_bridge import TradingAgentsBridge

        parsed = TradingAgentsBridge._parse(raw)
        assert parsed is not None
        assert parsed["bull_case"] == "a"

    def test_unparseable_output_is_rejected_rather_than_guessed(self):
        from app.services.tradingagents_bridge import TradingAgentsBridge

        assert TradingAgentsBridge._parse("I cannot help with that.") is None
