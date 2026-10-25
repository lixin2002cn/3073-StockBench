# Verification of the course starter

## Course time split, 25 October 2026

- 10 tests passed, including CLI date routing, rejection of mixed split/custom
  date options, and complete, non-overlapping coverage of the course period.
- The default CLI run now uses training/development (March–April). The named
  `validation` and `test` periods use May and June respectively.
- All three CLI runs completed with 20 stocks: 42, 21, and 20 daily observations.
  Their first/last trading dates were 3 March–30 April, 1–30 May, and 2–30 June.
  Each baseline run made 20 buy trades from a fresh account.
- An independent socket/DNS/UDP counter recorded zero network attempts across
  the three runs. No LLM client was imported and no model request was made.
- The audit receipt is [sample_outputs/course_split_audit.json](sample_outputs/course_split_audit.json).

The full-period results below and the saved `sample_outputs/equal_weight/`
example still describe March–June. They are illustrations, not an isolated
June test result. Model fitting and saved model state remain the strategy's
responsibility; `--split` selects the decision dates only.

## Original adaptation checks, 22 October 2026

Checked on 22 October 2026 on Windows with Python 3.13.5.

- 8 focused tests passed, covering strategy selection, cash budgets, costs,
  partial sales, position limits, data timing, network blocking and the LLM report switch.
- A fresh virtual environment containing only `requirements-offline.txt` and
  pytest ran the baseline. No OpenAI, Finnhub, Pydantic or HTTPX package was installed there.
- Full baseline: 20 stocks, 83 daily observations, 20 buy trades, no training.
- The independent network audit counted zero connection, DNS or UDP attempts.
- Independently summing cached prices, trade costs and cash dividends matched
  the engine's final equity: $100,845.00269719356 from $100,000 initial cash.
- The example custom momentum strategy also ran all 83 observations. Daily
  cash and holdings stayed nonnegative, and cash plus holdings matched equity.
- The original `llm_decision` strategy completed a 5-day, 2-stock integration
  check, with 5 stub decision calls and 6 trades. The stub replaced its model
  decision boundary. No real model request was made, so this does not verify a
  particular provider endpoint or model quality.

The saved baseline example is in `sample_outputs/equal_weight/`. These results
are examples, not target returns or grading thresholds.

## Tested offline dependencies

- numpy 2.5.4
- pandas 2.3.3
- pyarrow 22.0.0
- typer 0.27.3
- PyYAML 6.0.3
- loguru 0.7.3
- matplotlib 3.11.2

## Changes from the upstream snapshot

Upstream commit: `ce8b2b3483590646ad3b650ac8221f43f76fd091`.

The adaptation adds a strategy registry, a traditional baseline, a cached-only
reader, explicit network controls, and lazy optional imports. It also fixes
slippage cash accounting, combined-order budgets, increasing an existing
position at the position limit, sale cost records and future-priced snapshots.
CSV files, plots and detailed logs now share one output directory. Unknown
strategy names fail instead of silently selecting the LLM strategy.

The data files and upstream metrics definitions are retained. The corrected
execution rules can change results, so these are not an exact reproduction of
the paper's leaderboard. The cached archive does not certify point-in-time
correctness for every company indicator or remove a model's historical memory.
