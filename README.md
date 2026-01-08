# 📈 Leverage Strategy

A compact backtesting framework for medium-term trading strategies, built to evaluate leveraged exposures under severe drawdowns and crisis regimes. The engine explicitly models borrowed capital: borrowing interest is applied daily, so strategies that remain invested longer incur larger financing penalties. This design highlights trade-offs between aggressive leverage and time-at-risk during downturns.



## What this project does
- Generates synthetic leveraged NAVs from a base price series (e.g., market index such as S&P500) to simulate x2, x3,...
- Runs threshold-driven buying strategies that target purchases based on drawdowns and market-state signals (e.g., ma200, high-low).
- Evaluates strategy performance across multiple historical periods (including crisis windows), reporting profitability after fees and the cost of debt.
- Emphasizes time invested by charging a daily interest on borrowed capital, penalizing strategies that are invested longer.
- Automates the evaluation of multiple configurations (+1000) to get the best configuration in terms of CAGR, Adjusted CAGR, TUW...



## Quick guide

You must have `python >= 3.8` installed along with support with python virtual environment. To start the web service you just have to run the proper script depending on your operating system.

Windows:

```bat
.\run_app.bat
```

Linux:

```shell
./run_app.sh
```



## Key features

| Feature | Intent |
|---|---|
| Leveraged NAV construction | Create synthetic ETP-like NAVs from base series with compounding and TER applied daily. |
| Zero-knockout option | Model instruments that go to 0 after a large loss. Useful if the leveraged ETPs do not have an ["Air Bag" mechanism](https://leverageshares.com/en-eu/insights/the-air-bag-mechanism/). |
| Threshold entry policies | Buy rules driven by drawdown thresholds and configurable buy allocations. |
| Market-state detection | Identify crisis regimes using drawdown, moving averages and higher-low signals. |
| Debt modelling | Daily interest on borrowed capital to represent funding cost for leveraged positions. |
| Batch evaluation | Run many threshold configs over multiple historical periods and aggregate metrics for comparison. |



## Leverage & borrowing are modelling

- **Leverage**: Daily returns of the base series are multiplied by a leverage factor L, NAV evolves by compounding these leveraged daily returns. Then, volatility decay is properly emulated.
- **TER (total expense ratio)**: Applied as a daily multiplicative fee derived from an annual TER parameter.
- **Knockout behavior**: If enabled, negative daily factors can be floored to zero and the NAV remains zero afterwards (simulates an ETP that ceases to exist after severe losses).
- **Borrowing cost**: Debt is tracked and charged a daily interest rate (annualized input converted to daily). This cost is subtracted from gross value when computing net performance, so longer debt duration directly reduces net returns.



## Primary metrics reported

| Metric | Meaning |
|---|---|
| Gross value | Cash + current invested value (before debt and fees) |
| Debt cost | Total interest paid for financed capital over the backtest period |
| Fees paid | Trading fees applied |
| Net value | Gross value − debt cost − fees |
| Compound Annual Growth Rate (CAGR) | Annualized net return after fees and debt cost |
| Adjusted CAGR | CAGR adjusted by the number of days been invested |
| Time Under Water (TUW) | Number of days where the wallet's value is lower than initial capital over the total number of days in the backtest period |
| Baseline scenario | Buy-and-hold of base index (for comparison) |



## Important tabs

---

### 🧪 Backtest - Single backtest

Workflow:

1. Prepare base price series in the sidebar (CSV or download from Yahoo Finance).
2. Go to "🧪 Backtest" tab and configure strategy, that is, entry thresholds and yield/rotation/risk-control parameters.
3. Run backtest and see results.

**Relevant configuration knobs:**

| Parameter           | Impact                                                       |
| ------------------- | ------------------------------------------------------------ |
| Initial capital     | Starting cash for backtest (scales results)                  |
| Debt yield (annual) | Annual interest rate for debt, higher values penalize long-time investments |
| Entry thresholds    | Table indicating which percentage of initial capital should be invested in a specific asset when a drawdown is reached. |
| Rotate              | Add rotations between leverage factors instead of just buy and sell |
| Risk control        | Mechanism to avoid x3 ETF investing when market conditions suggest a crisis |

---

### 🧠 Evaluation - Multiple configurations

Workflow:

1. Prepare base price series in the sidebar (CSV or download from Yahoo Finance).
2. Go to "🧠 Evaluation" tab, just click "Evaluate" and wait.
3. Inspect logs, gross/net metrics, and comparative summaries vs baseline. You can see more details of the configurations tested under `src/evaluation/configs.py`.



## Development notes
- The framework is modular: add new entry rules or alternative risk controls and plug them into batch evaluation.
- Keep experiments reproducible: fix initial capital, debt yield, TER and evaluation windows when comparing strategies.
- Logs contain buy/sell traces — use them for debugging and post-mortem analysis of specific runs.
