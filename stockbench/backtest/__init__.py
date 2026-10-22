"""StockBench components, loaded only when requested."""
from importlib import import_module

_EXPORTS = {'BacktestEngine': ('engine', 'BacktestEngine'),
 'Datasets': ('datasets', 'Datasets'),
 'LlmDecision': ('strategies', 'LlmDecision'),
 'Portfolio': ('engine', 'Portfolio'),
 'PortfolioSnapshot': ('engine', 'PortfolioSnapshot'),
 'Position': ('engine', 'Position'),
 'Slippage': ('slippage', 'Slippage'),
 'TradeRecord': ('engine', 'TradeRecord'),
 'aggregate_with_rebalance': ('engine', 'aggregate_with_rebalance'),
 'align_with_strategy_nav': ('engine', 'align_with_strategy_nav'),
 'build_per_symbol_bh_benchmark': ('engine', 'build_per_symbol_bh_benchmark'),
 'compare_symbol_series': ('metrics', 'compare_symbol_series'),
 'compute_nav_to_metrics_series': ('metrics', 'compute_nav_to_metrics_series'),
 'compute_per_symbol_metrics_from_nav': ('metrics', 'compute_per_symbol_metrics_from_nav'),
 'compute_simple_average_benchmark': ('metrics', 'compute_simple_average_benchmark'),
 'compute_weighted_average_benchmark': ('metrics', 'compute_weighted_average_benchmark'),
 'evaluate': ('metrics', 'evaluate'),
 'extract_key_metrics_summary': ('metrics', 'extract_key_metrics_summary'),
 'generate_individual_stocks_summary': ('visualization', 'generate_individual_stocks_summary'),
 'load_benchmark_components': ('engine', 'load_benchmark_components'),
 'plot_aggregated_cumreturn_analysis': ('visualization', 'plot_aggregated_cumreturn_analysis'),
 'plot_multi_period_performance_heatmap': ('visualization',
                                           'plot_multi_period_performance_heatmap'),
 'plot_nav_comparison': ('visualization', 'plot_nav_comparison'),
 'plot_performance_ranking_over_time': ('visualization', 'plot_performance_ranking_over_time'),
 'plot_rolling_metrics_comparison': ('visualization', 'plot_rolling_metrics_comparison'),
 'plot_stock_price_trends': ('visualization', 'plot_stock_price_trends'),
 'plot_totalassets_comparison': ('visualization', 'plot_totalassets_comparison'),
 'price_to_returns': ('engine', 'price_to_returns'),
 'run_backtest': ('pipeline', 'run_backtest'),
 'summarize_backtest_results': ('summarize', 'main'),
 'write_outputs': ('reports', 'write_outputs')}
__all__ = list(_EXPORTS)

def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module, attr = _EXPORTS[name]
    value = getattr(import_module("." + module, __name__), attr)
    globals()[name] = value
    return value
