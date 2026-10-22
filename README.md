# DSAA3073 StockBench Starter

Build a trading method with traditional models, an LLM, or your own agent.
All methods use the same simulation engine and performance measures.
The released StockBench data is included, together with a simple baseline
that runs without training, an API key, or a model download.

[Project website](https://lixin2002cn.github.io/3073-Project/) ·
[Student quick start](STUDENT_QUICKSTART.md) ·
[Requirements & rubric](https://lixin2002cn.github.io/3073-Project/requirements.html) ·
[Download code & data](https://github.com/lixin2002cn/3073-StockBench/archive/refs/heads/main.zip)

## Start here

Download and extract the ZIP, or clone this repository. Use Python 3.10 or
newer. Open a terminal in the folder containing `configs/` and `stockbench/`.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-offline.txt
.\.venv\Scripts\python -m stockbench.apps.run_backtest --run-id my-first-run
```

macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-offline.txt
.venv/bin/python -m stockbench.apps.run_backtest --run-id my-first-run
```

Package installation needs internet access. After installation, this baseline
runs entirely offline. It buys equal dollar amounts of 20 stocks, leaves a
small cash reserve for costs, and holds them. The default period is March–June
2025, with 83 cached daily observations and $100,000 of starting cash.

Results go into `storage/reports/backtest/<run-id>/`. Open `equity.png`,
`metrics.json`, and `trades.csv` to see the account value, summary measures,
and executed trades. [Sample outputs](sample_outputs/equal_weight/) are
included.

## Bring your own method

| Method | Entry point |
| --- | --- |
| Offline baseline | [configs/offline_baseline.yaml](configs/offline_baseline.yaml) |
| Traditional or custom method | [examples/my_strategy.py](examples/my_strategy.py) |
| LLM or agent | [configs/llm_example.yaml](configs/llm_example.yaml) |
| Shared strategy interface | [Student quick start, section 2](STUDENT_QUICKSTART.md#2-add-your-own-method) |

A strategy implements `Strategy(cfg)` and `on_bar(ctx)`. It can return buy
and sell quantities, or use the helper that converts portfolio weights into
orders. The LLM route is optional and can use a local model server or a
compatible API. See the quick start for installation and configuration.

## What is included?

- Released local price, news, company-data, indicator, and corporate-action
  caches from StockBench.
- A common runner and trading engine, with trading costs, cash and holdings
  accounting, and saved results.
- An offline baseline, a custom strategy example, and the original LLM adapter.
- [Verification notes](VERIFICATION.md), tests, and scripts that check offline
  execution and account totals.

Historical data can be present in a model's training data. This starter does
not claim to remove that risk. Its simulation rules and information timing
are described in the quick start. **Profit and loss amounts do not affect
the project grade.**

## Source and license

This is the DSAA3073 course adaptation of
[ChenYXxxx/stockbench](https://github.com/ChenYXxxx/stockbench), based on commit
`ce8b2b3483590646ad3b650ac8221f43f76fd091`.
The upstream [Apache-2.0 license](LICENSE) and source attribution are retained.
Cached data keeps its original provider attribution and applicable terms.

The course adaptation adds a shared strategy interface and offline defaults,
and fixes several execution and output issues. Its results are not an exact
reproduction of the paper's leaderboard.

[Original documentation](UPSTREAM_README.md) ·
[StockBench research website](https://stockbench.github.io/) ·
[Paper](https://arxiv.org/abs/2510.02209)
