import os
import streamlit as st
import numpy as np

from src.backtest.strategy.Strategy import Strategy
from src.backtest.strategy.Asset import Asset
from src.backtest.strategy.Wallet import Wallet


class ThresholdsStrategy(Strategy):

    def __init__(self, total_eur, entry_thresholds, input_dfs, rotate, yield_targets, yield_values):
        super().__init__("Thresholds", total_eur, input_dfs)
        self.entry_thresholds = entry_thresholds
        self.rotate = rotate
        self.yield_targets = yield_targets
        self.yield_values = yield_values
        self.max_pcts = {}
        for dd, (buy_pct, buy_type) in self.entry_thresholds.items():
            if buy_type not in self.max_pcts:
                self.max_pcts[buy_type] = buy_pct
            if buy_pct > self.max_pcts[buy_type]:
                self.max_pcts[buy_type] = buy_pct

        # Initialise logs directory
        if not os.path.exists("logs") or not os.path.isdir("logs"):
            os.mkdir("logs")
        self.log_path = f"logs/thresholds.log"

    def get_amounts_to_buy(self, dd):
        # Get the percentage of total capital that should be invested in each type of asset for current drawdown
        buy_amounts = {}
        for pct, (buy_pct, buy_type) in self.entry_thresholds.items():
            if pct > dd:
                max_eur = self.max_pcts[buy_type] * self.total_eur
                buy_amounts[buy_type] = min(max(buy_amounts.get(buy_type, 0), buy_pct * self.total_eur), max_eur)
            else:
                break

        return buy_amounts

    def get_buys_to_sell(self, asset, t):
        return asset.check_buys_yields(t)

    def execute_sells(self, wallet, asset, lev_factor, buys_ready, t, current_dd, current_day, interactive):
        sells_counter = 0
        for i, buy in buys_ready.items():
            if interactive:
                print(f"SELL IN PROCESS @amount {buy['amount']}")
                _ = input("Enter to see result: ")

            prev_factor = self.get_prev_factor(lev_factor)
            prev_asset = wallet.get_asset(prev_factor)
            updated_idx = i - sells_counter
            amount = asset.sell_by_index(updated_idx, t)  # Sell shares from current lev factor
            sells_counter += 1
            # If there is a previous leverage factor and asset rotation is activated
            if prev_factor != "x1" and self.rotate:
                prev_asset.rotate_buy(asset.get_ticker(), amount, t, current_dd)
                wallet.track_rotate(f"{lev_factor} to {prev_factor}", current_day)
            # Otherwise, sell asset and accumulate cash or not leveraged ETF shares (x1)
            else:
                if wallet.cash + amount > self.total_eur:
                    earnings = wallet.cash + amount - self.total_eur
                    prev_asset.rotate_buy(asset.get_ticker(), earnings, t, current_dd)  # Invest earnings in x1
                    wallet.fill(self.total_eur)
                else:
                    wallet.receive(amount)
                wallet.track_sell(lev_factor, current_day)

    def buy_or_rotate(self, wallet, t, current_dd, current_day, interactive=False):
        target_investment_by_asset = self.get_amounts_to_buy(current_dd)
        for lev_factor, target_amount in target_investment_by_asset.items():
            asset = wallet.get_asset(lev_factor)
            invested_amount = asset.get_invested_eur()
            if target_amount > invested_amount:
                amount_to_invest = target_amount - invested_amount
                if interactive:
                    print(f"BUY IN PROCESS @amount {amount_to_invest}")
                    _ = input("Enter to see result: ")

                if self.rotate:
                    # FIRST, TRY TO ROTATE
                    prev_factor = self.get_prev_factor(lev_factor)
                    if prev_factor != "x1":
                        prev_asset = wallet.get_asset(prev_factor)
                        extra_cash = 0.0 if not prev_asset else prev_asset.get_extra_cash(t)
                        if extra_cash > 0.0:
                            amount_to_rotate = min(amount_to_invest, extra_cash)
                            prev_asset.rotate_down_sell(asset.get_ticker(), amount_to_rotate, t)
                            asset.rotate_buy(prev_asset.get_ticker(), amount_to_rotate, t, current_dd)
                            amount_to_invest -= amount_to_rotate
                            wallet.track_rotate(f"{prev_factor} to {lev_factor}", current_day)

                # BUY WITH CASH
                amount_to_invest = min(amount_to_invest, wallet.cash)
                if amount_to_invest > 0.0:
                    asset.buy(amount_to_invest, t, current_dd)
                    wallet.spend(amount_to_invest)
                    wallet.track_buy(lev_factor, current_day)

    def sell_or_rotate(self, wallet, t, current_dd, current_day, interactive=False):
        for lev_factor in ["x2", "x3"]:
            # Get asset from wallet
            asset = wallet.get_asset(lev_factor)

            # Check if the criteria to sell is matched
            buys_ready = self.get_buys_to_sell(asset, t)

            # Execute sells
            self.execute_sells(wallet, asset, lev_factor, buys_ready, t, current_dd, current_day, interactive)

    def backtest(self, interactive=False):
        # Clean log file from previous backtests
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

        # Convert time series DataFrames into numpy arrays (more efficient)
        days = self.input_dfs["x1"]['Days'].to_numpy(dtype=np.int64)
        prices, ath, dd, dmax = self.compute_drawdowns(self.input_dfs["x1"])
        prices_x2, ath_x2, dd_x2, dmax_x2 = self.compute_drawdowns(self.input_dfs["x2"])
        prices_x3, ath_x3, dd_x3, dmax_x3 = self.compute_drawdowns(self.input_dfs["x3"])

        # Initialise wallet
        wallet = Wallet(self.total_eur)
        wallet.add_asset("x1", Asset("S&P500 x1", prices, -1,  "none", -1, self.log_path))
        wallet.add_asset("x2", Asset("S&P500 x2", prices_x2, self.total_eur * self.max_pcts["x2"], self.yield_targets["x2"], self.yield_values["x2"], self.log_path))
        wallet.add_asset("x3", Asset("S&P500 x3", prices_x3, self.total_eur * self.max_pcts["x3"], self.yield_targets["x3"], self.yield_values["x3"], self.log_path))

        # Compute prices, ath, drawdowns and max drawdowns along the whole dataset
        for t in range(len(prices)):
            current_price = {"x1": prices[t], "x2": prices_x2[t], "x3": prices_x3[t]}
            current_dd = dd[t]
            current_dmax = dmax[t]
            current_day = days[t]

            if interactive:
                st.info(f"@iteration {t}: @price: {current_price['x1']} @dd: {current_dd} @dmax: {current_dmax}")
                st.info(f"@iteration {t}: @cash: {wallet.cash}")

            # BUY OR ROTATE
            self.buy_or_rotate(wallet, t, current_dd, current_day, interactive)

            # SELL OR ROTATE
            self.sell_or_rotate(wallet, t, current_dd, current_day, interactive)

        return wallet.to_dict()
