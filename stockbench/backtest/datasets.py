from __future__ import annotations

from typing import Dict, List

import pandas as pd


class Datasets:
	def __init__(self, cfg: Dict | None = None) -> None:
		self.cfg = cfg or {}

	def get_day_bars(self, symbol: str, start: str, end: str) -> pd.DataFrame:
		from stockbench.core import data_hub
		adjusted = True
		try:
			adjusted = bool(((self.cfg or {}).get("bars", {}) or {}).get("day", {}).get("adjusted", True))
		except Exception:
			adjusted = True
		return data_hub.get_bars(symbol, start, end, multiplier=1, timespan="day", adjusted=adjusted, cfg=self.cfg)

	def get_news(self, symbol: str, gte: str, lte: str) -> List[Dict]:
		from stockbench.core import data_hub
		data, _ = data_hub.get_news(symbol, gte, lte, limit=100, cfg=self.cfg)
		return data

	def get_dividends(self, symbol: str) -> pd.DataFrame:
		from stockbench.core import data_hub
		return data_hub.get_dividends(symbol, cfg=self.cfg)

	def get_splits(self, symbol: str) -> pd.DataFrame:
		from stockbench.core import data_hub
		return data_hub.get_splits(symbol, cfg=self.cfg)
