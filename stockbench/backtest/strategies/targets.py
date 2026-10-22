"""Helpers shared by small models, ensembles and agent strategies."""
import math


def orders_from_weights(ctx, weights, cash_buffer=0.01):
    """Convert long-only target weights to signed share changes.

    Weights sum to at most one. Missing symbols target zero. A small reserve
    covers fees, slippage and share rounding. Sells are returned before buys.
    """
    if not 0 <= cash_buffer < 1:
        raise ValueError("cash_buffer must be in [0, 1).")
    symbols = set(ctx["symbols"])
    if set(weights) - symbols:
        raise ValueError("Target contains a symbol outside the trading universe.")
    if any(not math.isfinite(float(w)) or w < 0 for w in weights.values()) or sum(weights.values()) > 1 + 1e-9:
        raise ValueError("Weights must be finite, nonnegative and sum to at most one.")
    pf = ctx["portfolio"]
    prices = ctx["open_map"]
    equity = pf.equity(prices)
    orders = []
    for symbol in ctx["symbols"]:
        price = float(prices[symbol])
        current = pf.positions[symbol].shares if symbol in pf.positions else 0.0
        target = math.floor(equity * (1 - cash_buffer) * weights.get(symbol, 0.0) / price * 100) / 100
        qty = round(target - current, 2)
        if qty:
            orders.append({"symbol": symbol, "qty": qty})
    return sorted(orders, key=lambda order: order["qty"] > 0)
