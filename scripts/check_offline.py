"""Audit a full offline baseline with an independent socket-call counter."""
import json
import math
from pathlib import Path
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import yaml
from stockbench.backtest.cached_datasets import CachedDatasets
from stockbench.backtest.pipeline import run_backtest
from stockbench.backtest.strategies import load_strategy
from stockbench.utils.logging_setup import setup_json_logging

cfg = yaml.safe_load((ROOT / "configs/offline_baseline.yaml").read_text())
setup_json_logging(cfg)
attempts = []
def blocked(*args, **kwargs):
    attempts.append(str(args[:1]))
    raise AssertionError("Offline baseline attempted a network operation")

# Keep the normal runtime guard off for this audit, so it cannot hide calls
# from the outer counter. Each attempted connection/DNS/UDP operation fails.
cfg["runtime"]["no_network"] = False
with patch.object(socket.socket, "connect", blocked), patch.object(socket.socket, "connect_ex", blocked), patch.object(socket, "create_connection", blocked), patch.object(socket, "getaddrinfo", blocked), patch.object(socket.socket, "sendto", blocked):
    result = run_backtest(cfg, load_strategy("equal_weight", cfg), "2025-03-01", "2025-06-30",
                          cfg["symbols_universe"], run_id="offline_audit")
assert not attempts, attempts
assert len(result["nav"]) == 83
trades = result["trades"]
assert len(trades) == 20 and (trades["side"] == "buy").all()
assert not any(m.startswith("stockbench.llm.") or m == "stockbench.core.data_hub" for m in sys.modules)

# Check the account against independent sums from the released prices and
# dividends, rather than merely trusting the engine's final NAV.
data = CachedDatasets(cfg)
cash = cfg["portfolio"]["total_cash"]
positions_value = 0.0
for row in trades.itertuples():
    opening = data.get_day_bars(row.symbol, "2025-03-03", "2025-03-03").iloc[0]["open"]
    assert math.isclose(row.exec_price, opening * 1.0002, rel_tol=1e-12)
    commission = row.qty * row.exec_price * .0001
    assert math.isclose(row.commission, commission, rel_tol=1e-12)
    cash -= row.qty * row.exec_price + commission
    dividends = data.get_dividends(row.symbol)
    for div in dividends.to_dict("records"):
        if "2025-03-03" < div.get("ex_dividend_date", "") <= "2025-06-30":
            cash += row.qty * float(div["cash_amount"])
    end_open = data.get_day_bars(row.symbol, "2025-06-30", "2025-06-30").iloc[0]["open"]
    positions_value += row.qty * end_open
last = result["portfolio_snapshots"][-1]
assert math.isclose(cash, last.cash, abs_tol=1e-7)
assert math.isclose(cash + positions_value, last.total_equity, abs_tol=1e-7)
assert all(s.cash >= 0 and all(p["shares"] >= 0 for p in s.positions.values())
           for s in result["portfolio_snapshots"])
assert not (Path(result["output_dir"]) / "nl_summary.txt").exists()
receipt = {"status": "passed", "symbols": 20, "daily_observations": 83, "trades": 20,
           "network_attempts": len(attempts), "real_model_calls": 0,
           "final_equity": last.total_equity, "independent_accounting_matches": True,
           "output_dir": result["output_dir"]}
(Path(result["output_dir"]) / "offline_audit.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt))
