import os
import streamlit as st
import numpy as np

from src.backtest.strategy.Strategy import Strategy
from src.backtest.strategy.Asset import Asset
from src.backtest.strategy.Wallet import Wallet


class ThresholdsStrategy(Strategy):

    def __init__(self, initial_capital, entry_thresholds, input_dfs, rotate, risk_control, yield_targets, yield_values, debt_yield):
        super().__init__("Thresholds", initial_capital, input_dfs)
        self.entry_thresholds = entry_thresholds
        self.rotate = rotate
        self.assets = sorted({asset for _, asset in entry_thresholds.values()})
        self.yield_targets = yield_targets
        self.yield_values = yield_values
        self.debt_yield = debt_yield
        self.max_pcts = {}
        self.market_state = "NORMAL"
        self.risk_control = risk_control
        self.change_counter = 0
        self.pause_x3 = False
        self.min_dd_seen = 0.0

        for buy_pct, buy_type in self.entry_thresholds.values():
            if buy_type not in self.max_pcts:
                self.max_pcts[buy_type] = buy_pct
            if buy_pct > self.max_pcts[buy_type]:
                self.max_pcts[buy_type] = buy_pct

        # Initialise logs directory
        if not os.path.exists("logs") or not os.path.isdir("logs"):
            os.mkdir("logs")
        self.log_path = f"logs/thresholds.log"

    def has_higher_low(self, prices, t, lookback=120):
        if t < lookback + 2:
            return False

        # Check from t - (lookback + 1) to t, we use (lookback +1) to check an earlier minimum
        window = prices[t-(lookback+1):(t+1)]

        # Create arrays shifted +1 and -1 position
        prev = window[:-2]
        curr = window[1:-1]
        next_ = window[2:]

        # Take all the values t that are lower than then previous (t-1) and next (t+1) values (local minimum)
        local_min_mask = (curr < prev) & (curr < next_)
        local_mins = curr[local_min_mask]

        if len(local_mins) < 2:
            return False

        # Check if the last minimum t is higher than the previous one t-1, indicating the trend may have changed
        return local_mins[-1] > local_mins[-2]

    def update_market_state(self, dd, prices, t):
        # Crisis is about to start
        if self.market_state == "NORMAL" and dd <= -0.10:
            self.market_state = "CRISIS"
            self.min_dd_seen = dd

        # Inside crisis
        elif self.market_state in ("CRISIS", "RECOVERY"):
            self.min_dd_seen = min(self.min_dd_seen, dd)

        # Recovering from crisis
        if self.market_state == "CRISIS" and self.has_higher_low(prices, t):
            self.market_state = "RECOVERY"

        # Come back to normal state
        if self.market_state == "RECOVERY" and dd > -0.15:
            self.market_state = "NORMAL"
            self.min_dd_seen = 0.0

    def update_x3_pause_state(self, dd, prices, t):
        #self.update_market_state(dd, prices, t)
        self.min_dd_seen = min(self.min_dd_seen, dd)
        price = prices[t]
        ma200 = prices[max(0, t-200):t+1].mean()

        pause_condition = (dd <= -0.35 and price < ma200 and not self.has_higher_low(prices, t))

        resume_condition = (price > ma200 and (dd - self.min_dd_seen) >= 0.10 and self.has_higher_low(prices, t))

        if not self.pause_x3 and pause_condition:
            self.change_counter += 1
            self.pause_x3 = True

        if self.pause_x3 and resume_condition:
            self.change_counter += 1
            self.min_dd_seen = 0.0  # Reset min_dd_seen as a recovery is considered
            self.pause_x3 = False

    def get_amounts_to_buy(self, dd):
        # Get the percentage of total capital that should be invested in each type of asset for current drawdown
        buy_amounts = {}
        for pct, (buy_pct, buy_type) in self.entry_thresholds.items():
            if pct > dd:
                if buy_type == "x3" and self.pause_x3:
                    continue
                max_eur = self.max_pcts[buy_type] * self.initial_capital
                buy_amounts[buy_type] = min(max(buy_amounts.get(buy_type, 0), buy_pct * self.initial_capital), max_eur)
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
            # Update index taking into account previous sells
            updated_idx = i - sells_counter
            # Sell the buy that has reached its yield target (by index)
            amount, fees = asset.sell_by_index(updated_idx, t)  # Sell shares from current lev factor
            wallet.pay_fees(fees)
            # Update the counter of performed sells
            sells_counter += 1
            # Look if the amount retrieved can be rotated to previous leverage factors
            prev_factor = self.get_prev_factor(lev_factor)
            # If there is a previous leverage factor and asset rotation is activated
            if prev_factor in self.assets and prev_factor != lev_factor and self.rotate:
                prev_asset = wallet.get_asset(prev_factor)
                fees = prev_asset.rotate_buy(asset.get_ticker(), amount, t, current_dd)
                wallet.pay_fees(fees)
                wallet.track_rotate(f"{lev_factor} to {prev_factor}", current_day)
            # Otherwise, sell asset and accumulate cash or not leveraged ETF shares (x1)
            else:
                if wallet.cash + amount > self.initial_capital:
                    earnings = wallet.cash + amount - self.initial_capital
                    prev_asset = wallet.get_asset("x1_save")
                    fees = prev_asset.rotate_buy(asset.get_ticker(), earnings, t, current_dd)  # Invest earnings in x1
                    wallet.track_buy("x1_save", current_day)
                    wallet.fill(self.initial_capital)
                    wallet.pay_fees(fees)
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

                # FIRST, TRY TO ROTATE
                prev_factor = self.get_prev_factor(lev_factor)
                if prev_factor in self.assets and prev_factor != lev_factor and self.rotate:
                    prev_asset = wallet.get_asset(prev_factor)
                    extra_cash = 0.0 if not prev_asset else prev_asset.get_extra_cash(t)
                    if extra_cash > 0.0:
                        amount_to_rotate = min(amount_to_invest, extra_cash)
                        sell_fees = prev_asset.sell_amount(amount_to_rotate, t, asset.get_ticker())
                        buy_fees = asset.rotate_buy(prev_asset.get_ticker(), amount_to_rotate, t, current_dd)
                        amount_to_invest -= amount_to_rotate
                        wallet.track_rotate(f"{prev_factor} to {lev_factor}", current_day)
                        wallet.pay_fees(sell_fees + buy_fees)

                # BUY WITH CASH
                amount_to_invest = min(amount_to_invest, wallet.cash)
                if amount_to_invest > 0.0:
                    fees = asset.buy(amount_to_invest, t, current_dd)
                    wallet.spend(amount_to_invest)
                    wallet.pay_fees(fees)
                    wallet.track_buy(lev_factor, current_day)

    def sell_or_rotate(self, wallet, t, current_dd, current_day, interactive=False):
        for lev_factor in self.assets:
            # Get asset from wallet
            asset = wallet.get_asset(lev_factor)

            # Check if the criteria to sell is matched
            buys_ready = self.get_buys_to_sell(asset, t)

            # Execute sells
            self.execute_sells(wallet, asset, lev_factor, buys_ready, t, current_dd, current_day, interactive)

    def compute_debt_costs(self, wallet):
        owed_money = self.initial_capital - wallet.cash
        if owed_money > 0.0:
            wallet.track_debt_time(1)  # +1 day with debt
            if self.debt_yield > 0.0:
                # In the mortgage agreement they use 360 to compute interest costs
                daily_debt_cost = owed_money * self.debt_yield / 360
                wallet.track_debt_cost(daily_debt_cost)

        if wallet.get_total_value() < self.initial_capital:
            wallet.track_time_under_water(1)  # +1 day under water

    def backtest(self, interactive=False):
        # Clean log file from previous backtests
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

        # Convert time series DataFrames into numpy arrays (more efficient)
        days = self.input_dfs["x1"]['Days'].to_numpy(dtype=np.int64)
        prices, ath, dd, dmax = self.compute_drawdowns(self.input_dfs["x1"])
        prices_dict, ath_dict, dd_dict, dmax_dict = {}, {}, {}, {}
        for asset in self.assets:
            prices_dict[asset], ath_dict[asset], dd_dict[asset], dmax_dict[asset] = self.compute_drawdowns(self.input_dfs[asset])

        # Initialise wallet
        wallet = Wallet(self.initial_capital)
        wallet.add_asset("x1_save", Asset("S&P500 x1", prices, -1,  "none", -1, self.log_path))
        for asset in self.assets:
            wallet.add_asset(asset, Asset(f"S&P500 {asset}", prices_dict[asset], self.initial_capital * self.max_pcts[asset], self.yield_targets[asset], self.yield_values[asset], self.log_path))

        # Compute prices, ath, drawdowns and max drawdowns along the whole dataset
        for t in range(len(prices)):
            current_dd, current_dmax, current_day = dd[t], dmax[t], days[t]

            if interactive:
                st.info(f"@iteration {t}: @price: {prices[t]} @dd: {current_dd} @dmax: {current_dmax}")
                st.info(f"@iteration {t}: @cash: {wallet.cash}")

            # Update x3 pause logic (only needs x1 prices)
            if self.risk_control:
                self.update_x3_pause_state(current_dd, prices, t)

            # BUY OR ROTATE
            self.buy_or_rotate(wallet, t, current_dd, current_day, interactive)

            # SELL OR ROTATE
            self.sell_or_rotate(wallet, t, current_dd, current_day, interactive)

            # Add debt financial costs (daily interest rate)
            self.compute_debt_costs(wallet)

        return wallet.to_dict()
