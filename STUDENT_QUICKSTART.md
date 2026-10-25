# StockBench course starter

Use a traditional method, an LLM, or your own agent. All strategies use the
same trading engine and metrics. This starter includes the released data.

## 1. Run the offline baseline

Use Python 3.10 or newer. Python 3.11 or 3.12 is a good choice. Open a terminal
in this folder, where `configs/` and `stockbench/` are visible.

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

Installing Python packages needs internet access unless you already have the
packages. After installation, the baseline runs entirely offline. It needs
no API key, model download, model server, or training. It does not read keys
from an `.env` file.

The default configuration is `configs/offline_baseline.yaml`. It starts with
$100,000, buys equal dollar amounts of the 20 configured stocks on the first
trading day, keeps about 1% cash for costs, then holds. The default run uses
March–April 2025, the training/development period, with 42 trading days.
Commission is 1 basis point and slippage is 2 basis points per trade. One basis
point is 0.01%. These are teaching settings, not estimates of every real cost.

The terminal prints the output folder. Open these files there:

| File | What it shows |
| --- | --- |
| `equity.png` | Portfolio value over time |
| `metrics.json` | Return, maximum drawdown and other metrics |
| `daily_nav.csv` | Daily portfolio value divided by initial cash |
| `trades.csv` | Executed trades, prices and commissions |
| `detailed_portfolio_snapshots.jsonl` | Daily cash and holdings |
| `detailed_trading_summary.json` | Initial cash and final portfolio value |

Outputs are normally under `storage/reports/backtest/<run-id>/`. Reusing a run
ID creates a new folder with a time suffix. Existing results are preserved.

### Course dates: train, validate, then test

Use the same time split for all methods. The full course period has 83 trading
days. Weekend and holiday dates do not create trading observations.

| Phase | Calendar range, 2025 | Trading days | Purpose |
| --- | --- | ---: | --- |
| Training / Development | 1 March–30 April | 42 | Fit a model, develop a rule, or write a prompt |
| Validation | 1–31 May | 21 | Compare methods and choose settings |
| Test | 1–30 June | 20 | Report the final result after choosing your method |

After activating your virtual environment, run:

```sh
python -m stockbench.apps.run_backtest --split train --run-id train
python -m stockbench.apps.run_backtest --split validation --run-id validation
python -m stockbench.apps.run_backtest --split test --run-id test
```

Without activation, replace `python` with `.\.venv\Scripts\python` on Windows
or `.venv/bin/python` on macOS/Linux. Add the same `--strategy` and `--cfg`
options to run your own method in each period. With no date options, the
runner uses `train`.

`--split` selects dates only. It does not fit, select, or save a model. Each
command creates a new strategy instance and a fresh account with the configured
starting cash (default $100,000). Load any trained model or saved learning
state in your own strategy. Do not carry cash or stock positions across these
separate runs. Earlier cached observations may supply a past-only feature
window; check the availability time of each feature and training label.

Choose your method, settings, initial prompt, and online update rule before the test
period. During June, online learning may use feedback only after it becomes
available. Do not replay June to select a better method or settings. Keep the
dates in time order; do not randomly shuffle them. These are public historical
data, so the test period is not a hidden or contamination-free test set.

Training a new model is optional. Rules, traditional models, LLMs, and agents
all use these periods. Profit and loss amounts do not affect your grade.

For a shorter development run, use custom dates instead of `--split`:

```sh
python -m stockbench.apps.run_backtest --start 2025-03-03 --end 2025-03-07 --run-id small-check
```

Do not combine `--split` with `--start` or `--end`. A missing custom boundary
uses the training period's boundary. Dates only select the decision period;
the downloaded archive remains readable and is not a future-data sandbox.

## 2. Add your own method

The strategy interface is `Strategy(cfg)` with a method `on_bar(ctx)`. It
returns a list of orders. Positive `qty` buys shares. Negative `qty` sells.
Return `[]` to keep the current holdings. Use at most one order per stock per
call. Quantities have two decimal places. Short sales and borrowing are not
supported in this starter.

```python
class Strategy:
    def __init__(self, cfg):
        self.cfg = cfg

    def on_bar(self, ctx):
        # Example: buy one share only if no shares of this stock are held.
        symbol = ctx["symbols"][0]
        position = ctx["portfolio"].positions.get(symbol)
        if position is None or position.shares == 0:
            return [{"symbol": symbol, "qty": 1.0}]
        return []
```

Save it as `my_method.py` in this folder. Then run:

```sh
python -m stockbench.apps.run_backtest --strategy my_method:Strategy --run-id my-method
```

Use your environment's Python executable if you did not activate the virtual
environment. `examples/my_strategy.py` is another runnable example. It uses
past price momentum and the shared `orders_from_weights(ctx, weights)` helper:

```sh
python -m stockbench.apps.run_backtest --strategy examples.my_strategy:Strategy --run-id momentum
```

These are examples to show the interface. You choose the question, method and
analysis for your project.

### Information in `ctx`

- `date`: the current decision date.
- `symbols`: the trading universe.
- `open_map`: current opening prices, used as the execution reference.
- `portfolio`: current cash and positions.
- `history`: daily price frames strictly before the current decision date,
  available in the offline data mode. The default is the last 30 observations.
- `datasets`: the data reader. For example,
  `ctx["datasets"].get_news(symbol, "2025-04-01", "2025-04-04")` returns cached
  news from 1 to 3 April and excludes 4 April. Missing news can produce an empty list.

The underlying reader can access the whole downloaded archive. It is not a
hidden-test sandbox. Only request information available at the decision time.
Do not use today's high, low, close or volume to decide a trade at today's
open. Historical financial indicators and model memory need their own checks.

## 3. Use an LLM or agent

The original `llm_decision` strategy remains available. Install its optional
dependencies in your environment:

```sh
python -m pip install -r requirements.txt
```

For a compatible local model server, edit `configs/llm_example.yaml`: set its
model name and server URL. Start with two stocks and five days:

```sh
python -m stockbench.apps.run_backtest --cfg configs/llm_example.yaml --llm-profile local_model --end 2025-03-07 --run-id llm-small
```

A local model server is a separate service. This command does not install or
start one. For a remote provider, set the profile's `provider` to `openai`,
set its compatible `base_url` and model name, set `auth_required: true`, and
provide `OPENAI_API_KEY` through your shell. Keep keys out of code and Git.
The profile is a connection setting, not a course restriction on model choice.

You can also implement your own LLM or agent as `package.module:Strategy`.
Its final output still uses the same signed-share order interface. The original
agent can make several model requests per day, so begin with a short run.

### Data offline versus all network disabled

| Setting | Meaning |
| --- | --- |
| `--offline` or `data.mode: offline_only` | Read market data from local caches. Model calls may still use a server. |
| `--no-network` or `runtime.no_network: true` | Also block Python socket connections, DNS and UDP sends. Reject the built-in LLM strategy and LLM reports in the CLI. |
| `--allow-network` | Override the all-network block. It does not change the offline market-data setting. |

The offline baseline sets `no_network: true` and `summary_llm: false`. The LLM
example keeps market data offline but allows model-server connections. Reports
do not call an LLM unless `summary_llm` is explicitly enabled. The network
guard is a check against accidental calls, not a security sandbox for untrusted
code or external subprocesses.

## 4. Read results with the simulation rules in mind

Strategies decide once at the current open. Orders use that opening reference
plus slippage. Cash pays both execution cost and commission. Daily NAV and
snapshots use the current open, including on the final date. Final holdings
are not automatically sold. The simulation assumes a fill at the opening
reference even though the method observes it, as in the supplied engine.

Cached corporate actions use the upstream convention: splits adjust shares,
and cash dividends enter the account on the ex-dividend date. Missing price
files fail rather than triggering a paid data API. Metrics keep StockBench's
definitions, including its Sortino calculation.

This adaptation fixes several execution and output issues in the downloaded
code. Its results are not an exact reproduction of the paper's leaderboard.
The CLI follows the course periods above; `--split` selects the decision
dates. The reader still requires you to respect the information cutoff.
Profit and loss amounts do not determine the project grade.

## Checks

```sh
python -m pip install pytest
python -m pytest tests -q
```

With the optional LLM dependencies installed, `python scripts/check_llm_adapter.py`
checks the original LLM strategy with fake decisions at the model boundary.
It never calls a real model. `python scripts/check_offline.py` audits a complete
baseline run and checks that it makes zero Python network attempts.

Upstream: https://github.com/ChenYXxxx/stockbench, commit
`ce8b2b3483590646ad3b650ac8221f43f76fd091`. The upstream Apache-2.0 license
and data-source attribution remain in the package.
