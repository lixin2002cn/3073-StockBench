"""Read only the released files. Missing market data never triggers an API."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd


class CachedDatasets:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        default = Path(__file__).resolve().parents[2] / "storage"
        self.root = Path(self.cfg.get("data", {}).get("storage_dir", default))
        self._bars = {}

    def _load_bars(self, symbol):
        if symbol not in self._bars:
            paths = sorted((self.root / "parquet" / symbol / "day").glob("*.parquet"))
            if not paths:
                raise FileNotFoundError(f"No cached daily prices for {symbol} under {self.root}.")
            # Upstream stores one tiny file per day. Parallel reads avoid slow
            # startup on Windows and network-mounted student folders.
            with ThreadPoolExecutor(max_workers=8) as pool:
                frame = pd.concat(list(pool.map(pd.read_parquet, paths)), ignore_index=True)
            frame["date"] = pd.to_datetime(frame["date"]).dt.date
            if frame["date"].duplicated().any():
                raise ValueError(f"Duplicate daily prices for {symbol}.")
            self._bars[symbol] = frame.sort_values("date").reset_index(drop=True)
        return self._bars[symbol]

    def get_day_bars(self, symbol, start, end):
        frame = self._load_bars(symbol)
        a, b = pd.Timestamp(start).date(), pd.Timestamp(end).date()
        return frame.loc[frame["date"].between(a, b)].copy()

    def trading_dates(self, symbols, start, end):
        frames = [self.get_day_bars(s, start, end) for s in symbols]
        dates = sorted(set().union(*(set(f["date"]) for f in frames)))
        if not dates:
            raise ValueError("No cached trading dates in the requested range.")
        for s, f in zip(symbols, frames):
            missing = set(dates) - set(f["date"])
            if missing:
                raise ValueError(f"Missing cached prices for {s}: {sorted(missing)[:5]}")
            full = self._load_bars(s)
            # Weekend boundaries are allowed, silent truncation outside coverage is not.
            weekdays = pd.bdate_range(start, end)
            if len(weekdays) and (weekdays[0].date() < full["date"].min() or weekdays[-1].date() > full["date"].max()):
                raise ValueError(f"Requested range exceeds cached price coverage for {s}.")
        return pd.DatetimeIndex(dates)

    def history(self, symbol, decision_date, days=30):
        """Only completed daily bars strictly before the decision date."""
        frame = self._load_bars(symbol)
        return frame.loc[frame["date"] < pd.Timestamp(decision_date).date()].tail(days).copy()

    def get_news(self, symbol, gte, lte):
        """lte is the decision date and is excluded, matching the upstream rule."""
        items = {}
        for day in pd.date_range(gte, lte, inclusive="left"):
            path = self.root / "cache" / "news_by_day" / symbol / f"{day:%Y-%m-%d}.json"
            if not path.exists():
                continue
            for item in json.loads(path.read_text(encoding="utf-8")).get("items", []):
                when = pd.to_datetime(item.get("published_utc"), utc=True, errors="coerce")
                if pd.isna(when) or not pd.Timestamp(gte, tz="UTC") <= when < pd.Timestamp(lte, tz="UTC"):
                    continue
                key = item.get("id") or item.get("url") or (item.get("title"), str(when))
                items[key] = item
        return sorted(items.values(), key=lambda x: x.get("published_utc", ""), reverse=True)

    def _actions(self, symbol, kind):
        path = self.root / "cache" / "corporate_actions" / f"{symbol}.{kind}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing corporate-action cache: {path}")
        return pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))

    def get_dividends(self, symbol):
        return self._actions(symbol, "dividends")

    def get_splits(self, symbol):
        return self._actions(symbol, "splits")
