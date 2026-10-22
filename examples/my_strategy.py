"""A simple past-only momentum example. Replace it with your own method."""
from stockbench.backtest.strategies.targets import orders_from_weights


class Strategy:
    def __init__(self, cfg):
        self.lookback = int(cfg.get("strategy", {}).get("lookback", 20))

    def on_bar(self, ctx):
        selected = []
        for symbol, history in ctx["history"].items():
            closes = history["close"].tail(self.lookback)
            if len(closes) == self.lookback and closes.iloc[-1] > closes.iloc[0]:
                selected.append(symbol)
        weights = {s: 1 / len(selected) for s in selected}
        return orders_from_weights(ctx, weights)
