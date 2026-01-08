"""
Batch evaluation of multiple entry_threshold configurations over multiple historical periods.

This module is meant to be IMPORTED and called from Streamlit.
It does NOT contain Streamlit code itself.

Expected responsibilities:
- Iterate over threshold configurations (list[pd.DataFrame])
- Iterate over predefined periods
- Run the backtest engine you already have
- Aggregate results into clean summary tables

You only need to adapt ONE function call:
    run_backtest_for_period(...)
so it connects with your existing backtest logic.
"""

from dataclasses import dataclass
import pandas as pd

from src.utils.utils import _leverage_dataset

# ============================================================
# Static configuration values
# ============================================================
INITIAL_CAPITAL = 10000
DEBT_YIELD = 0.0325


@dataclass
class BacktestSummary:
    period: str
    cash: float
    fees: float
    debt_cost: float
    debt_time: int
    gross_value: float
    tuw: float
    cagr: float
    adjusted_cagr: float
    base_debt_time: int
    base_debt_cost: float
    base_scenario: float
    base_cagr: float


def retrieve_backtest_results(strategy, input_data):
    result = strategy.backtest()

    # Get elapsed time and price movement over period
    x1 = input_data["x1"]
    first_price, last_price = x1.loc[x1['Date'].idxmin(), 'Adj Close'], x1.loc[x1['Date'].idxmax(), 'Adj Close']
    start_day, end_day = int(x1['Days'].min()), int(x1['Days'].max())
    elapsed_days = end_day - start_day

    # Compute additional metrics
    result["gross_value"] = result["cash"] + sum([result[a].get_invested_value() for a in result["assets"]])
    result["tuw"] /= elapsed_days  # Normalise value as a percentage of total number of days
    net_value = result["gross_value"] - result["debt_cost"] - result["fees_paid"]
    result["cagr"] = (max(net_value, 0.0) / INITIAL_CAPITAL) ** (365 / elapsed_days) - 1
    result["adjusted_cagr"] = (max(net_value, 0.0) / INITIAL_CAPITAL) ** (365 / result["debt_time"]) - 1 if result["debt_time"] > 0 else result["cagr"]

    # Add baseline scenario metrics
    result["base_scenario"] = INITIAL_CAPITAL * last_price / first_price
    result["base_debt_time"] = elapsed_days
    result["base_debt_cost"] = INITIAL_CAPITAL * elapsed_days * (DEBT_YIELD / 360)
    net_value = result["base_scenario"] - result["base_debt_cost"] - max(INITIAL_CAPITAL * 0.0012, 1.0)
    result["base_cagr"] = (max(net_value, 0.0) / INITIAL_CAPITAL) ** (365 / elapsed_days) - 1

    return result


def get_input_data(config_assets, df, start_dt, end_dt):
    input_data = {"x1": df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt)].copy()}
    for asset in config_assets:
        if asset == "x1":
            continue
        input_data[asset] = _leverage_dataset(input_data["x1"], L=int(asset[-1]), knockout_zero=True)
    return input_data


def evaluate_threshold_config(strategy_builder, df, periods, config_values) -> pd.DataFrame:
    # Dynamic values
    entry_thresholds = config_values["thresholds"]
    rotate = config_values["rotate"]
    risk_control = config_values["risk_control"]
    yield_targets = config_values["yield_targets"]
    yield_values = config_values["yield_values"]

    summaries = []
    for period_name, (start, end) in periods.items():
        # Get input data for this period
        start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
        assets = sorted({asset for _, asset in entry_thresholds.values()})
        input_data = get_input_data(assets, df, start_dt, end_dt)

        # Initialise strategy
        strategy = strategy_builder(INITIAL_CAPITAL, entry_thresholds, input_data, rotate, risk_control, yield_targets, yield_values, DEBT_YIELD)

        # Backtest strategy and retrieve results
        metrics = retrieve_backtest_results(strategy, input_data)

        summaries.append(
            BacktestSummary(
                period=period_name,
                cash=metrics["cash"],
                fees=metrics["fees_paid"],
                debt_cost=metrics["debt_cost"],
                debt_time=metrics["debt_time"],
                gross_value=metrics["gross_value"],
                cagr=metrics["cagr"],
                adjusted_cagr=metrics["adjusted_cagr"],
                tuw=metrics["tuw"],
                base_debt_time=metrics["base_debt_time"],
                base_debt_cost=metrics["base_debt_cost"],
                base_scenario=metrics["base_scenario"],
                base_cagr=metrics["base_cagr"],
            )
        )
    return pd.DataFrame([s.__dict__ for s in summaries])


def evaluate_all_configurations(strategy_builder, configs, periods, df):
    results = {}
    for name, config in configs.items():
        results[name] = evaluate_threshold_config(strategy_builder, df, periods, config)

    return results
