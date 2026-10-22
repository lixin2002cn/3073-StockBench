"""Buy equal dollar amounts once, then hold. No training or model calls."""
from .targets import orders_from_weights


class Strategy:
    def __init__(self, cfg):
        self.cfg = cfg

    def on_bar(self, ctx):
        if any(p.shares > 0 for p in ctx["portfolio"].positions.values()):
            return []
        symbols = ctx["symbols"]
        return orders_from_weights(ctx, {s: 1 / len(symbols) for s in symbols},
                                   cash_buffer=self.cfg.get("strategy", {}).get("cash_buffer", 0.01))
