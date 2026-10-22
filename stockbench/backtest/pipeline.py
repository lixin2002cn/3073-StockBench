from __future__ import annotations

from typing import Dict, List, Optional
import os

from stockbench.backtest.datasets import Datasets
from stockbench.backtest.engine import BacktestEngine
from stockbench.backtest.slippage import Slippage
from stockbench.backtest.reports import write_outputs


def run_backtest(cfg: Dict, strategy, start: str, end: str, symbols: List[str], run_id: str | None = None, timespan: Optional[str] = None) -> Dict:
    from stockbench.core.network import no_network
    if cfg.get("runtime", {}).get("no_network", False):
        if cfg.get("backtest", {}).get("summary_llm", False):
            raise ValueError("LLM reports require network access.")
        cfg.setdefault("data", {})["mode"] = "offline_only"
    with no_network(cfg.get("runtime", {}).get("no_network", False)):
        return _run_backtest(cfg, strategy, start, end, symbols, run_id, timespan)


def _run_backtest(cfg, strategy, start, end, symbols, run_id, timespan):
    if cfg.get("data", {}).get("mode") == "offline_only":
        from stockbench.backtest.cached_datasets import CachedDatasets
        datasets = CachedDatasets(cfg)
    else:
        datasets = Datasets(cfg)
    slippage = Slippage.from_cfg(cfg)
    engine = BacktestEngine(cfg, datasets, slippage)
    # Write detailed logs into the same unique directory as metrics and CSVs.
    engine.enable_detailed_logging = False
    # Select timespan: prioritize CLI input; otherwise read from config; finally fallback to "day"
    effective_timespan = (timespan or (cfg.get("backtest", {}) or {}).get("timespan") or "day")
    # Run backtest
    result = engine.run(strategy=strategy, start=start, end=end, symbols=symbols, timespan=effective_timespan, run_id=run_id)
    if result["trades"].empty:
        result["trades"] = result["trades"].reindex(columns=["ts", "symbol", "side", "qty", "exec_price", "commission"])
    # Write timespan back to cfg for report display
    try:
        cfg.setdefault("backtest", {})["timespan"] = effective_timespan
    except Exception:
        pass
    out_dir = write_outputs(result, run_id=run_id, cfg=cfg)
    result["output_dir"] = out_dir
    if cfg.get("backtest", {}).get("enable_detailed_logging", False):
        engine.enable_detailed_logging = True
        engine._save_trading_logs(result.get("trade_records", []), result.get("portfolio_snapshots", []), out_dir)
    result["nav"].rename("nav").to_csv(os.path.join(out_dir, "daily_nav.csv"))
    result["trades"].to_csv(os.path.join(out_dir, "trades.csv"), index=False)
    if not bool(cfg.get("backtest", {}).get("summary_llm", False)):
        return result
    if cfg.get("runtime", {}).get("no_network", False):
        raise ValueError("LLM report generation is incompatible with no_network.")
    from stockbench.agents.backtest_report_llm import generate_backtest_report
    # Backtest natural language summary (as part of the backtest process)
    try:
        # Read summary.txt content (if exists) and assemble richer payload
        summary_txt_path = os.path.join(out_dir, "summary.txt")
        summary_text = ""
        try:
            if os.path.exists(summary_txt_path):
                with open(summary_txt_path, "r", encoding="utf-8") as f:
                    summary_text = f.read()
        except Exception:
            summary_text = ""
        metrics_dict = result.get("metrics") or {}
        payload = {
            "metrics": metrics_dict,
            "summary_text": summary_text,
            "period": {"start": start, "end": end},
            "timespan": effective_timespan,
            "run_id": run_id or os.path.basename(out_dir),
            "symbols": symbols,
        }
        # Get LLM profile name from configuration
        profile_name = None
        try:
            profiles = cfg.get("llm_profiles", {})
            if profiles:
                # Prioritize openai profile (if exists)
                if "openai" in profiles:
                    profile_name = "openai"
                else:
                    # Otherwise use the first available profile
                    profile_name = next(iter(profiles.keys()))
        except Exception:
            pass
            
        text = generate_backtest_report(payload, cfg=cfg, run_id=run_id, profile_name=profile_name)
        nl_path = os.path.join(out_dir, "nl_summary.txt")
        with open(nl_path, "w", encoding="utf-8") as f:
            f.write(text)
        result["nl_summary"] = nl_path
    except Exception:
        pass
    return result
