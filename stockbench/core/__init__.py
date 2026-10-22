"""Core components with lazy optional model and provider imports."""
from importlib import import_module

_EXPORTS = {'AnalyzerOutput': ('schemas', 'AnalyzerOutput'),
 'DecisionOutput': ('schemas', 'DecisionOutput'),
 'FeatureInput': ('schemas', 'FeatureInput'),
 'NewsSnapshot': ('schemas', 'NewsSnapshot'),
 'Order': ('schemas', 'Order'),
 'PositionState': ('schemas', 'PositionState'),
 'TechSnapshot': ('schemas', 'TechSnapshot'),
 'add_price_fallback_mechanism': ('price_utils', 'add_price_fallback_mechanism'),
 'build_features_for_prompt': ('features', 'build_features_for_prompt'),
 'calculate_position_value': ('price_utils', 'calculate_position_value'),
 'clear_old_news_cache': ('data_hub', 'clear_old_news_cache'),
 'compare_with_legacy_day': ('data_hub', 'compare_with_legacy_day'),
 'decide_batch': ('executor', 'decide_batch'),
 'get_bars': ('data_hub', 'get_bars'),
 'get_cache_info': ('data_hub', 'get_cache_info'),
 'get_dividends': ('data_hub', 'get_dividends'),
 'get_financials': ('data_hub', 'get_financials'),
 'get_gainers_losers': ('data_hub', 'get_gainers_losers'),
 'get_grouped_daily': ('data_hub', 'get_grouped_daily'),
 'get_market_status': ('data_hub', 'get_market_status'),
 'get_news': ('data_hub', 'get_news'),
 'get_next_trading_day': ('data_hub', 'get_next_trading_day'),
 'get_splits': ('data_hub', 'get_splits'),
 'get_stock_indicators': ('data_hub', 'get_stock_indicators'),
 'get_ticker_details': ('data_hub', 'get_ticker_details'),
 'get_unified_price': ('price_utils', 'get_unified_price'),
 'get_universal_snapshots': ('data_hub', 'get_universal_snapshots'),
 'is_trading_day': ('data_hub', 'is_trading_day'),
 'plan_orders': ('executor', 'plan_orders'),
 'validate_price_data_consistency': ('price_utils', 'validate_price_data_consistency')}
__all__ = list(_EXPORTS)

def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module, attr = _EXPORTS[name]
    value = getattr(import_module("." + module, __name__), attr)
    globals()[name] = value
    return value
