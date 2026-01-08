from math import floor


class Asset:

    def __init__(self, ticker, prices, max_eur, yield_target, yield_value, log_file, allow_fractional=True, min_trade_value=5.0):
        self.ticker = ticker
        self.prices = prices
        self.max_eur = max_eur
        self.yield_target = yield_target  # "none", "num" or "auto"
        self.yield_value = -1 if yield_target == "none" else yield_value
        self.log_file = log_file
        self.invested_eur = 0
        self.invested_qty = 0
        self.invested_value = 0
        self.buys = []
        self.allow_fractional = allow_fractional
        self.min_trade_value = float(min_trade_value)

    def __log_and_print(self, msg):
        with open(self.log_file, "a") as f:
            f.write(f"{msg}\n")
        #print(msg)

    def __get_yield_value(self, dd):
        if self.yield_target == "auto":
            return (1 / (1 + dd)) - 1  # Yield to recover 100% of current dropdown
        return self.yield_value

    def __get_invested_value(self, t):
        return self.invested_qty * self.prices[t]

    def __get_buy(self, idx):
        if idx >= len(self.buys):
            raise IndexError(f"Index out of range when accessing {self.ticker} buys list: Index={idx} | Length={len(self.buys)}")
        return self.buys[idx]

    def __update_buy(self, idx, item):
        if idx >= len(self.buys):
            raise IndexError(f"Index out of range when accessing {self.ticker} buys list: Index={idx} | Length={len(self.buys)}")
        self.buys[idx] = item

    def __delete_buy(self, idx):
        if idx >= len(self.buys):
            raise IndexError(f"Index out of range when accessing {self.ticker} buys list: Index={idx} | Length={len(self.buys)}")
        del self.buys[idx]

    def __create_buy(self, t, amount, fees, qty, dd):
        return {
            "index": t,
            "ticker": self.ticker,
            "price": self.prices[t],
            "amount": amount,
            "qty": qty,
            "fees": fees,
            "yield_value": self.__get_yield_value(dd),
            "current_dd": dd,
            "invested_eur": self.invested_eur,
            "pending_until_max": max(self.max_eur - self.invested_eur, 0) if self.max_eur > 0 else -1
        }

    def __print_buy(self, buy_item):
        self.__log_and_print("************************ BUY ************************")
        self.__log_and_print(f"{'Ticker':<30}: {buy_item['ticker']:>10}")
        self.__log_and_print(f"{'Buy time':<30}: {buy_item['index']:>10}")
        self.__log_and_print(f"{'Price':<30}: {buy_item['price']:>10.2f}")
        self.__log_and_print(f"{'Amount':<30}: {buy_item['amount']:>10.2f}")
        self.__log_and_print(f"{'Quantity':<30}: {buy_item['qty']:>10.2f}")
        self.__log_and_print(f"{'Fees':<30}: {buy_item['fees']:>10.2f}")
        self.__log_and_print(f"{'Yield target':<30}: {buy_item['yield_value']:>10.2f}")
        self.__log_and_print(f"{'Current drawdown':<30}: {buy_item['current_dd']:>10.2f}")
        self.__log_and_print(f"{'Invested EUR (after buy)':<30}: {self.invested_eur:>10.2f}")
        self.__log_and_print(f"{'Pending until max':<30}: {buy_item['pending_until_max']:>10.2f}")
        self.__log_and_print("*****************************************************")

    def __print_sell(self, buy_item, sell_time, sell_price, final_amount, fees, final_yield):
        self.__log_and_print("************************ SELL ************************")
        self.__log_and_print(f"{'Ticker':<30}: {buy_item['ticker']:>10}")
        self.__log_and_print(f"{'Buy time':<30}: {buy_item['index']:>10}")
        self.__log_and_print(f"{'Buy Price':<30}: {buy_item['price']:>10.2f}")
        self.__log_and_print(f"{'Sell time':<30}: {sell_time:>10}")
        self.__log_and_print(f"{'Sell price':<30}: {sell_price:>10.2f}")
        self.__log_and_print(f"{'Initial amount':<30}: {buy_item['amount']:>10.2f}")
        self.__log_and_print(f"{'Final amount':<30}: {final_amount:>10.2f}")
        self.__log_and_print(f"{'Fees':<30}: {fees:>10.2f}")
        self.__log_and_print(f"{'Yield target':<30}: {buy_item['yield_value']:>10.2f}")
        self.__log_and_print(f"{'Final yield':<30}: {final_yield:>10.2f}")
        self.__log_and_print(f"{'Invested EUR (after sell)':<30}: {self.invested_eur:>10.2f}")
        self.__log_and_print("*****************************************************")

    def __print_partial_sell(self, buy_item, sell_time, sell_price, sell_qty, final_amount, fees, final_yield):
        self.__log_and_print("******************** PARTIAL SELL ********************")
        self.__log_and_print(f"{'Ticker':<30}: {buy_item['ticker']:>10}")
        self.__log_and_print(f"{'Buy time':<30}: {buy_item['index']:>10}")
        self.__log_and_print(f"{'Buy Price':<30}: {buy_item['price']:>10.2f}")
        self.__log_and_print(f"{'Sell time':<30}: {sell_time:>10}")
        self.__log_and_print(f"{'Sell price':<30}: {sell_price:>10.2f}")
        self.__log_and_print(f"{'Initial amount':<30}: {buy_item['amount']:>10.2f}")
        self.__log_and_print(f"{'Sold amount':<30}: {(sell_qty*buy_item['price']):>10.2f}")
        self.__log_and_print(f"{'Final amount':<30}: {final_amount:>10.2f}")
        self.__log_and_print(f"{'Fees':<30}: {fees:>10.2f}")
        self.__log_and_print(f"{'Yield target':<30}: {buy_item['yield_value']:>10.2f}")
        self.__log_and_print(f"{'Final yield':<30}: {final_yield:>10.2f}")
        self.__log_and_print(f"{'Invested EUR (after sell)':<30}: {self.invested_eur:>10.2f}")
        self.__log_and_print("*****************************************************")

    def __add_buy_item(self, amount_eur, fees, t, dd):
        # Compute invested qty
        qty = amount_eur / self.prices[t] if self.prices[t] > 0 else 0.0

        # Update cummulative amounts
        self.invested_eur += amount_eur
        self.invested_qty += qty
        self.invested_value = self.prices[t] * self.invested_qty

        # Create and add buy
        new_buy = self.__create_buy(t, amount_eur, fees, qty, dd)
        self.buys.append(new_buy)
        return new_buy

    def __buy(self, amount_eur, t, dd):
        price = self.prices[t]
        if price <= 0:
            self.__log_and_print(f"Price for {self.ticker} at {t} is non-positive. Skipping buy.")
            return None

        # Avoid micro-trades
        if amount_eur < self.min_trade_value:
            self.__log_and_print(f"Buy amount {amount_eur}€ for {self.ticker} under min_trade_value {self.min_trade_value}. Skipping.")
            return None

        # Adjust amount if fractional shares are not allowed
        if not self.allow_fractional:
            qty = int(floor(amount_eur / price))
            if qty <= 0:
                self.__log_and_print(f"Desired buy {amount_eur}€ for {self.ticker} too small to buy 1 share at price {price:.2f}. Skipping.")
                return None
            amount_eur = qty * price

        # Compute fees (recomputed after rounding)
        fees = self.compute_fees(amount_eur)

        # Add buy
        buy_item = self.__add_buy_item(amount_eur, fees, t, dd)

        return buy_item

    @staticmethod
    def compute_fees(amount):
        return max(amount * 0.0012, 1.0)

    def get_ticker(self):
        return self.ticker

    def get_invested_eur(self):
        return self.invested_eur

    def get_price(self, t):
        return self.prices[t]

    def get_last_price(self):
        return self.prices[-1]

    def get_invested_value(self, t=None):
        if t is None:
            return self.invested_qty * self.prices[-1]
        return self.invested_qty * self.prices[t]

    def get_buys(self):
        return self.buys

    def get_extra_cash(self, t):
        self.invested_value = self.invested_qty * self.prices[t]
        return max(self.invested_value - self.max_eur, 0)

    # Buy shares using cash
    def cash_buy(self, amount_eur, t, dd):
        # Check investment upper limit is not surpassed (max_eur should be >0, -1 means there is no limit)
        if 0 < self.max_eur < self.invested_eur + amount_eur:
            raise ValueError(f"Trying to buy more than {self.max_eur} of {self.ticker} using cash. Aborting...")

        # Add buy
        buy_item = self.__buy(amount_eur, t, dd)
        if buy_item is None:
            return False, 0.0

        # Print buy info
        self.__log_and_print(f"Using cash to buy {amount_eur}€ of {self.ticker}")
        self.__print_buy(buy_item)

        return True, buy_item['fees']

    # Buy shares by rotating from higher leverage factors
    def rotate_buy(self, from_ticker, amount_eur, t, dd):
        # Add buy
        buy_item = self.__buy(amount_eur, t, dd)
        if buy_item is None:
            return False, 0.0

        # Print buy info
        self.__log_and_print(f"Rotating {amount_eur}€ from {from_ticker} to {self.ticker}")
        self.__print_buy(buy_item)

        return True, buy_item['fees']

    # Sell shares to rotate to higher leverage factors
    def sell_amount(self, amount_eur, t, to_ticker=None):
        if amount_eur > self.__get_invested_value(t):
            raise ValueError(f"Trying to sell {amount_eur} from {self.ticker} but current invested value is lower: {self.__get_invested_value(t)}")

        # Avoid micro-trades
        if amount_eur < self.min_trade_value:
            self.__log_and_print(f"Sell amount {amount_eur}€ for {self.ticker} under min_trade_value {self.min_trade_value}. Skipping.")

        pending_amount = amount_eur
        current_price = self.prices[t]
        total_fees = 0.0
        while pending_amount > 0.0:
            # Exit condition, no more buys to sell
            if len(self.buys) == 0:
                break

            # Get the older buy first (FIFO)
            buy_item = self.__get_buy(0)
            buy_value = current_price * buy_item['qty']
            sell_amount = min(buy_value, pending_amount)

            # If fractional shares are not allowed, when the amount is smaller than 1 share price, the sell is finished
            sell_qty = sell_amount / current_price if current_price > 0 else 0.0
            if not self.allow_fractional:
                sell_qty = int(floor(sell_qty))
                if sell_qty <= 0:
                    self.__log_and_print(f"Desired sell {sell_amount}€ for {self.ticker} too small to sell 1 "
                                         f"share at price {current_price:.2f}. Skipping.")
                    break
                sell_amount = sell_qty * current_price

            final_yield = (current_price / buy_item['price']) - 1

            # Update quantities using buy price for invested_eur
            self.invested_eur -= sell_qty * buy_item['price']
            self.invested_qty -= sell_qty
            self.invested_value = current_price * self.invested_qty

            # Logging
            if to_ticker is None:
                self.__log_and_print(f"Selling {sell_amount}€ from {self.ticker}")
            else:
                self.__log_and_print(f"Rotating {sell_amount}€ from {self.ticker} to {to_ticker}")

            # Update fees
            sell_fees = self.compute_fees(sell_amount)
            total_fees += sell_fees

            if sell_amount >= buy_value:
                # Full buy sold
                self.__print_sell(buy_item, t, current_price, sell_amount, sell_fees, final_yield)
                self.__delete_buy(0)
            else:
                # Partial sell
                self.__log_and_print(f"Partial sell of {self.ticker} amount = {sell_amount}€ (shares value = {buy_value}€)")
                self.__print_partial_sell(buy_item, t, current_price, sell_qty, sell_amount, sell_fees, final_yield)
                buy_item['qty'] -= sell_qty
                buy_item['amount'] = buy_item['qty'] * buy_item['price']
                self.__update_buy(0, buy_item)

            pending_amount -= sell_amount

        return amount_eur - pending_amount, total_fees

    def sell_by_index(self, idx, t):
        buy_item = self.__get_buy(idx)
        buy_qty, buy_price, buy_amount = buy_item['qty'], buy_item['price'], buy_item['amount']
        current_price = self.prices[t]
        final_yield = (current_price / buy_price) - 1
        final_amount = current_price * buy_qty

        self.invested_eur -= buy_amount
        self.invested_qty -= buy_qty
        self.invested_value = current_price * self.invested_qty
        fees = self.compute_fees(final_amount)  # Compute fees

        self.__log_and_print(f"Selling {buy_amount}€ of {self.ticker} that has reached its yield target")
        self.__print_sell(buy_item, t, current_price, final_amount, fees, final_yield)

        self.__delete_buy(idx)

        return final_amount, fees

    def check_buys_yields(self, t):
        buys_ready = {}
        current_price = self.prices[t]
        if self.yield_target != "none":
            for i, buy in enumerate(self.buys):
                if (current_price / buy['price']) - 1 > buy['yield_value']:
                    buys_ready[i] = buy
        return buys_ready


