import socket
import sys
from datetime import timedelta
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest
import yaml
from typer.testing import CliRunner

from stockbench.apps.run_backtest import app
from stockbench.backtest.cached_datasets import CachedDatasets
from stockbench.backtest.engine import BacktestEngine
from stockbench.backtest.pipeline import run_backtest
from stockbench.backtest.slippage import Slippage
from stockbench.backtest.strategies import load_strategy
from stockbench.core.network import NetworkDisabledError, no_network

ROOT = Path(__file__).resolve().parents[1]


def config():
    return yaml.safe_load((ROOT / "configs/offline_baseline.yaml").read_text())


class TinyData:
    def __init__(self):
        self.dates = pd.date_range("2025-03-03", periods=3, freq="B")

    def trading_dates(self, symbols, start, end):
        return self.dates

    def get_day_bars(self, symbol, start, end):
        # Reading tomorrow would fail. Intraday highs/closes are deliberately
        # very different from the open to expose a wrong valuation convention.
        d = pd.Timestamp(start)
        assert start == end and d in self.dates
        i = self.dates.get_loc(d)
        return pd.DataFrame([{"date": d.date(), "open": [100., 120., 80.][i], "close": 9999.}])

    def history(self, symbol, date, days):
        return pd.DataFrame({"date": [pd.Timestamp(date).date() - timedelta(days=1)], "close": [50.]})

    def get_dividends(self, symbol):
        return pd.DataFrame()

    def get_splits(self, symbol):
        return pd.DataFrame()


def engine(cfg=None):
    cfg = cfg or config()
    cfg["backtest"]["enable_detailed_logging"] = False
    return BacktestEngine(cfg, TinyData(), Slippage.from_cfg(cfg))


def test_cash_slippage_partial_sale_and_snapshot_timing():
    class RoundTrip:
        def on_bar(self, ctx):
            assert all(d < ctx["date"].date() for d in ctx["history"]["A"]["date"])
            return [{"symbol": "A", "qty": [2., -1., -1.][ctx["date"].day - 3]}]

    cfg = config()
    cfg["portfolio"]["total_cash"] = 1000
    cfg["backtest"].update(commission_bps=10, slippage_bps=100)
    result = engine(cfg).run(RoundTrip(), "2025-03-03", "2025-03-05", ["A"])
    expected_cash = 1000 - 2 * 101 * 1.001 + 118.8 * .999 + 79.2 * .999
    snapshots = result["portfolio_snapshots"]
    assert snapshots[-1].cash == pytest.approx(expected_cash)
    assert snapshots[-1].positions == {}
    assert snapshots[1].positions["A"]["total_cost"] == pytest.approx(101 * 1.001)
    assert result["nav"].iloc[0] == pytest.approx((1000 - 202 * 1.001 + 200) / 1000)
    assert snapshots[0].positions["A"]["mark_price"] == 100
    assert result["trades"]["exec_price"].tolist() == pytest.approx([101, 118.8, 79.2])
    assert result["trades"]["commission"].sum() == pytest.approx((202 + 118.8 + 79.2) * .001)
    assert sum(t.realized_pnl for t in result["trade_records"]) == pytest.approx(expected_cash - 1000)


def test_combined_budget_and_no_short_positions():
    class TooMuch:
        def on_bar(self, ctx):
            return [{"symbol": s, "qty": 9} for s in ctx["symbols"]]
    cfg = config()
    cfg["portfolio"]["total_cash"] = 1000
    r = engine(cfg).run(TooMuch(), "2025-03-03", "2025-03-05", ["A", "B"])
    assert all(s.cash >= 0 for s in r["portfolio_snapshots"])
    assert len(r["portfolio_snapshots"][0].positions) == 1

    class Short:
        def on_bar(self, ctx):
            return [{"symbol": "A", "qty": -1}]
    with pytest.raises(ValueError, match="more shares than held"):
        engine().run(Short(), "2025-03-03", "2025-03-05", ["A"])


def test_existing_position_can_increase_at_position_limit():
    class Add:
        def on_bar(self, ctx):
            return [{"symbol": "A", "qty": 1}]
    cfg = config()
    cfg["risk"]["max_positions"] = 1
    r = engine(cfg).run(Add(), "2025-03-03", "2025-03-05", ["A"])
    assert r["portfolio_snapshots"][-1].positions["A"]["shares"] == 3


def test_factory_rejects_unknown_and_accepts_custom_and_llm(monkeypatch):
    with pytest.raises(ValueError, match="Unknown strategy"):
        load_strategy("typo", {})
    assert callable(load_strategy("examples.my_strategy:Strategy", {}).on_bar)
    # Exercise the LLM registry route without importing provider libraries or
    # making a model request. The actual legacy module remains available.
    fake = ModuleType("stockbench.backtest.strategies.llm_decision")
    class FakeLLM:
        def __init__(self, cfg):
            self.cfg = cfg
        def on_bar(self, ctx):
            return []
    fake.Strategy = FakeLLM
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    assert isinstance(load_strategy("llm_decision", {}), FakeLLM)


def test_network_guard_blocks_and_restores_socket():
    original = socket.create_connection
    with no_network():
        with pytest.raises(NetworkDisabledError):
            socket.create_connection(("example.invalid", 443))
        with pytest.raises(NetworkDisabledError):
            socket.getaddrinfo("example.invalid", 443)
    assert socket.create_connection is original


def test_llm_summary_cannot_bypass_no_network(tmp_path, monkeypatch):
    cfg = config()
    cfg["backtest"]["summary_llm"] = True
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="LLM reports require"):
        run_backtest(cfg, load_strategy("equal_weight", cfg), "2025-03-03", "2025-03-07", ["AAPL"], "blocked_report")
    assert not (tmp_path / "storage").exists()


def test_released_data_offline_no_llm_report_or_network(tmp_path, monkeypatch):
    cfg = config()
    monkeypatch.chdir(tmp_path)
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append(args)
        raise AssertionError("Unexpected network connection")
    # Audit outside the runtime guard as well: there must be zero attempts,
    # not merely exceptions swallowed by the upstream report code.
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    cfg["runtime"]["no_network"] = False
    strat = load_strategy("equal_weight", cfg)
    r = run_backtest(cfg, strat, "2025-03-03", "2025-03-07", ["AAPL", "MSFT"], run_id="smoke")
    assert attempts == []
    assert len(r["nav"]) == 5
    assert len(r["trades"]) == 2
    assert "stockbench.agents.backtest_report_llm" not in sys.modules
    out = Path(r["output_dir"])
    for name in ["metrics.json", "daily_nav.csv", "trades.csv", "detailed_portfolio_snapshots.jsonl"]:
        assert (out / name).is_file()
    assert not (out / "nl_summary.txt").exists()
    assert len(list((tmp_path / "storage/reports/backtest").iterdir())) == 1


def test_cache_cutoff_missing_data_and_cli_errors():
    data = CachedDatasets(config())
    assert all(d < pd.Timestamp("2025-04-04").date() for d in data.history("AAPL", "2025-04-04")["date"])
    assert all(pd.Timestamp(n["published_utc"]) < pd.Timestamp("2025-04-04")
               for n in data.get_news("AAPL", "2025-04-02", "2025-04-04"))
    with pytest.raises(FileNotFoundError):
        data.get_day_bars("NOT_A_SYMBOL", "2025-03-03", "2025-03-04")
    result = CliRunner().invoke(app, ["--cfg", str(ROOT / "configs/offline_baseline.yaml"), "--strategy", "typo"])
    assert result.exit_code != 0 and "Unknown strategy" in result.output
    result = CliRunner().invoke(app, ["--cfg", str(ROOT / "configs/offline_baseline.yaml"), "--strategy", "llm_decision"])
    assert result.exit_code != 0 and "allow-network" in result.output
