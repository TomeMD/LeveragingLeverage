import time
import pandas as pd
import streamlit as st
from src.evaluation.batch_evaluation import evaluate_all_configurations
from src.backtest.strategy.builders import STRATEGY_BUILDERS
from src.evaluation.configs import build_all_configurations, PERIODS

SCORE_FORMULA = [
    {"weight": 2.0, "metric": "cagr"},
    {"weight": -0.5, "metric": "tuw"},
]


def asc_is_better(metric):
    if metric == "tuw":
        return True
    return False


def flatten_results(results):
    dfs = []
    for config_name, df in results.items():
        df = df.copy()
        df["config"] = config_name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def compute_score(df, formula, normalizer):
    score = 0.0
    for term in formula:
        score += term["weight"] * normalizer(df[term["metric"]])

    return score


def formula_str(formula, normalizer_name="min-max normalized"):
    terms = []

    for term in formula:
        w = term["weight"]
        metric = term["metric"].replace("_", " ").upper()

        sign = "" if w > 0 else "−"
        abs_w = abs(w)

        terms.append(f"- {sign} {abs_w:g} × {metric}")

    body = "\n".join(terms)

    return (
        f"Score is computed as a weighted sum of {normalizer_name} metrics:\n\n"
        f"{body}\n\n"
        f"Higher score = better overall strategy performance."
    )


def augment_metrics(df):
    df = df.copy()

    df["excess_cagr"] = df["cagr"] - df["base_cagr"]
    df["value_vs_base"] = df["gross_value"] / df["base_scenario"]

    def minmax(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-9)

    df["score"] = compute_score(df, SCORE_FORMULA, minmax)

    return df


def show_global_kpis(ref_metric, df):
    best_config = df.groupby("config")[ref_metric].mean().sort_values(ascending=asc_is_better(ref_metric)).index[0]

    best_df = df[df["config"] == best_config]

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("🏆 Best config", best_config, help=best_config)

    c2.metric("Avg CAGR", f"{best_df['cagr'].mean():.2%}", help="Compound Annual Growth Rate (CAGR)")
    c3.metric("Avg Adjusted CAGR", f"{best_df['adjusted_cagr'].mean():.2%}", help="CAGR adjusted by the amount of days invested")
    c4.metric("Avg debt cost", f"{best_df['debt_cost'].mean():,.0f} €")
    c5.metric("Avg score", f"{best_df['score'].mean():.2f}", help=formula_str(SCORE_FORMULA))
    c6.metric("Avg TUW", f"{best_df['tuw'].mean():.2%}", help="Time Under Water (TUW)")
    c7.metric("Worst period score", f"{best_df['score'].min():.2f}")


def show_global_ranking(ref_metric, df):
    ranking = (
        df.groupby("config")
        .agg(
            avg_score=("score", "mean"),
            avg_cagr=("cagr", "mean"),
            avg_tuw=("tuw", "mean"),
            avg_excess_cagr=("excess_cagr", "mean"),
            worst_score=("score", "min"),
            max_debt_cost=("debt_cost", "max"),
        )
        .sort_values(f"avg_{ref_metric}", ascending=asc_is_better(ref_metric))
        .round(3)
    )

    st.subheader("🏆 Global configuration ranking")
    st.dataframe(
        ranking.style
        .background_gradient(subset=["avg_score"], cmap="RdYlGn")
        .background_gradient(subset=["worst_score"], cmap="RdYlGn"),
        width='stretch'
    )


def show_best_by_period(ref_metric, df):
    best = df.sort_values(ref_metric, ascending=asc_is_better(ref_metric)).groupby("period").first().reset_index()

    st.subheader("📆 Best configuration per period")
    st.dataframe(
        best[[
            "period",
            "config",
            "cagr",
            "tuw",
            "debt_cost",
            "debt_time",
            "score"
        ]].round(3),
        width='stretch'
    )


def show_heatmap(ref_metric, df):
    pivot = df.pivot(
        index="config",
        columns="period",
        values=ref_metric
    )
    # Compute average score per config
    avg_score = (df.groupby("config")[ref_metric].mean().sort_values(ascending=asc_is_better(ref_metric)))

    # Reorder pivot rows by average score
    pivot = pivot.loc[avg_score.index]

    st.subheader(f"🔥 Strategy robustness heatmap ({ref_metric})")
    st.dataframe(
        pivot.style.background_gradient(cmap="RdYlGn"),
        width='stretch'
    )


def show_config_drilldown(df):
    st.subheader("🔍 Configuration drill-down")

    config = st.selectbox(
        "Select configuration",
        options=sorted(df["config"].unique())
    )

    st.dataframe(
        df[df["config"] == config]
        .sort_values("period"),
        width='stretch'
    )


def run():
    if not st.session_state.get('df_loaded', False):
        st.info("Upload a CSV file or download the data from Yahoo Finance")
        st.stop()

    # Get DataFrame from session state
    df = st.session_state["df"]

    # Select strategy to evaluate
    strategy_key = st.selectbox(
        "Investment strategy",
        options=list(STRATEGY_BUILDERS.keys()),
        format_func=lambda k: {
            "thresholds": "Threshold-based buys + Yield-based sales",
        }[k],
    )

    evaluate = st.button("▶ Evaluate strategy")
    if evaluate:
        if st.session_state.get('strategy_key', '') != strategy_key:
            st.session_state.strategy_key = strategy_key
        strategy_builder = STRATEGY_BUILDERS[st.session_state.strategy_key]

        with st.spinner(f"Building configurations..."):
            configs = build_all_configurations()

        start = time.time()
        with st.spinner(f"Evaluating {len(configs)} configurations..."):
            results = evaluate_all_configurations(strategy_builder, configs, PERIODS, df)
            st.session_state.evaluation_results = results
        end = time.time()
        st.info(f"Successfully evaluated {len(configs)} configurations in {end - start:>.2f} seconds")


    # Show results
    if st.session_state.get('evaluation_results') is not None:
        # Select reference metric to choose best strategy
        ref_metric = st.selectbox(
            "Reference metric",
            options=["score", "cagr", "adjusted_cagr", "tuw"],
            format_func=lambda k: {"score": "Score", "cagr": "CAGR", "adjusted_cagr": "Adjusted CAGR", "tuw": "TUW"}[k],
        )

        global_results = flatten_results(st.session_state.evaluation_results)
        global_results = augment_metrics(global_results)

        st.divider()
        show_global_kpis(ref_metric, global_results)

        st.divider()
        show_global_ranking(ref_metric, global_results)

        st.divider()
        show_best_by_period(ref_metric, global_results)

        st.divider()
        show_heatmap(ref_metric, global_results)

        st.divider()
        show_config_drilldown(global_results)
