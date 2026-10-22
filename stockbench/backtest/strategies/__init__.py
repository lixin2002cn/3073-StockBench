"""Select a strategy without importing optional LLM dependencies."""
from importlib import import_module


def load_strategy(name, cfg):
    builtins = {
        "equal_weight": "stockbench.backtest.strategies.equal_weight:Strategy",
        "llm_decision": "stockbench.backtest.strategies.llm_decision:Strategy",
    }
    target = builtins.get(name, name)
    if ":" not in target:
        raise ValueError(f"Unknown strategy {name!r}. Use equal_weight, llm_decision, or package.module:Strategy.")
    module_name, class_name = target.rsplit(":", 1)
    strategy = getattr(import_module(module_name), class_name)(cfg)
    if not callable(getattr(strategy, "on_bar", None)):
        raise TypeError(f"{target} must implement on_bar(ctx).")
    return strategy


def __getattr__(name):
    if name == "LlmDecision":
        return import_module(".llm_decision", __name__).Strategy
    raise AttributeError(name)


__all__ = ["load_strategy", "LlmDecision"]
