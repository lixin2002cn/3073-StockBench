"""Optional integration smoke test. Uses the real LLM strategy with a stub
at its model-decision boundary, never a real model/API request.
Run with the full requirements installed: python scripts/check_llm_adapter.py
"""
import json
import logging
import os
from pathlib import Path
import socket
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["TA_DATA_MODE"] = "offline_only"
os.environ["POLYGON_API_KEY"] = ""
os.environ["FINNHUB_API_KEY"] = ""

import yaml
from loguru import logger
logger.remove()
logging.basicConfig(level=logging.ERROR)

attempts, calls = [], []
def blocked(*args, **kwargs):
    attempts.append(args)
    raise AssertionError("Unexpected network attempt in the LLM adapter check")

def fake_decisions(features_list, cfg=None, **kwargs):
    calls.append(len(features_list))
    return {f["symbol"]: {"action": "increase", "target_cash_amount": 1000,
                            "confidence": 0.5, "reason": "integration test stub"}
            for f in features_list}

with patch.object(socket.socket, "connect", blocked), patch.object(socket, "create_connection", blocked):
    from stockbench.backtest.strategies import load_strategy
    from stockbench.backtest.pipeline import run_backtest
    cfg = yaml.safe_load((ROOT / "configs/offline_baseline.yaml").read_text())
    cfg["runtime"]["no_network"] = False  # outer audit catches any attempt
    cfg["agents"]["mode"] = "dual"
    with patch("stockbench.backtest.strategies.llm_decision.unified_decide_batch", fake_decisions):
        strategy = load_strategy("llm_decision", cfg)
        old_cwd = Path.cwd()
        with TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                result = run_backtest(cfg, strategy, "2025-03-03", "2025-03-07", ["AAPL", "MSFT"], "llm_stub")
            finally:
                os.chdir(old_cwd)
    assert calls and len(result["nav"]) == 5
    assert len(result["trades"]) > 0
    assert attempts == []
    print(json.dumps({"status": "passed", "strategy": "original llm_decision",
                      "trading_days": len(result["nav"]), "decision_stub_calls": len(calls),
                      "trades": len(result["trades"]), "network_attempts": len(attempts),
                      "real_model_calls": 0}))
