import os

class Asset:

    def __init__(self, ticker, prices, max_eur, yield_target, yield_value, log_file):
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

    def __get_yield_value(self, dd):
        if self.yield_target == "auto":
            return (1 / (1 + dd)) - 1  # Yield to recover 100% of current dropdown
        return self.yield_value

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

    def __log_and_print(self, msg):
        with open(self.log_file, "a") as f:
            f.write(f"{msg}\n")
        #print(msg)

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

    def __add_buy(self, amount_eur, fees, t, dd):
        # Compute invested qty
        # TODO: Compute real amount because we cannot invest fractional amounts
        qty = amount_eur / self.prices[t]

        # Update cummulative amounts
        self.invested_eur += amount_eur
        self.invested_qty += qty
        self.invested_value = self.prices[t] * self.invested_qty

        # Create and add buy
        self.buys.append(self.__create_buy(t, amount_eur, fees, qty, dd))

    # Buy shares using cash
    def buy(self, amount_eur, t, dd):
        # Check investment upper limit is not surpassed (max_eur should be >0, -1 means there is no limit)
        if 0 < self.max_eur < self.invested_eur + amount_eur:
            raise ValueError(f"Trying to buy more than {self.max_eur} of {self.ticker} using cash. Aborting...")

        # Compute fees
        fees = self.compute_fees(amount_eur)

        # Add buy
        self.__add_buy(amount_eur, fees, t, dd)

        # Print buy info
        self.__log_and_print(f"Using cash to buy {amount_eur}€ of {self.ticker}")
        self.__print_buy(self.buys[-1])

        return fees

    # Buy shares by rotating from higher leverage factors
    def rotate_buy(self, from_ticker, amount_eur, t, dd):
        # Compute fees
        fees = self.compute_fees(amount_eur)

        # Add buy
        self.__add_buy(amount_eur, fees, t, dd)

        # Print buy info
        self.__log_and_print(f"Rotating {amount_eur}€ from {from_ticker} to {self.ticker}")
        self.__print_buy(self.buys[-1])

        return fees

    # Sell shares to rotate to higher leverage factors
    def sell_amount(self, amount_eur, t, to_ticker=None):
        if amount_eur > self.invested_value:
            raise ValueError(f"Trying to sell {amount_eur} from {self.ticker} but current invested value is lower: {self.invested_value}")
        pending_amount = amount_eur
        current_price = self.prices[t]
        fees = self.compute_fees(amount_eur)  # Compute fees
        while pending_amount > 0.0:
            if len(self.buys) == 0:
                break
            buy_item = self.buys[0] # FIFO
            buy_value = current_price * buy_item['qty']
            sell_amount = min(buy_value, pending_amount)
            sell_qty = sell_amount / current_price
            final_yield = (current_price / buy_item['price']) - 1

            self.invested_eur -= sell_qty * buy_item['price'] # We remove the value at the time of buying, not the current value
            self.invested_qty -= sell_qty
            self.invested_value = current_price * self.invested_qty

            if to_ticker is None:
                self.__log_and_print(f"Selling {sell_amount}€ from {self.ticker}")
            else:
                self.__log_and_print(f"Rotating {sell_amount}€ from {self.ticker} to {to_ticker}")
            sell_fees = self.compute_fees(sell_amount)
            if sell_amount >= buy_value:
                self.__print_sell(buy_item, t, current_price, sell_amount, sell_fees, final_yield)
                del self.buys[0]
            else:
                self.__log_and_print(f"Partial sell of {self.ticker} amount = {sell_amount}€ (shares value = {buy_value}€)")
                self.__print_partial_sell(buy_item, t, current_price, sell_qty, sell_amount, sell_fees, final_yield)
                self.buys[0]['qty'] -= sell_qty
                self.buys[0]['amount'] = self.buys[0]['qty'] * self.buys[0]['price']

            pending_amount -= sell_amount

        return fees

    def sell_by_index(self, idx, t):
        buy_item = self.buys[idx]
        qty = buy_item['qty']
        buy_price = buy_item['price']
        current_price = self.prices[t]
        target_yield = buy_item['yield_value']
        final_yield = (current_price / buy_price) - 1
        initial_amount = buy_item['amount']
        final_amount = current_price * qty
        buy_time = buy_item['index']


        self.invested_eur -= initial_amount
        self.invested_qty -= qty
        self.invested_value = current_price * self.invested_qty
        fees = self.compute_fees(final_amount)  # Compute fees

        self.__log_and_print(f"Selling {initial_amount}€ of {self.ticker} that has reached its yield target")
        self.__print_sell(buy_item, t, current_price, final_amount, fees, final_yield)

        del self.buys[idx]

        return final_amount, fees

    def check_buys_yields(self, t):
        buys_ready = {}
        current_price = self.prices[t]
        if self.yield_target != "none":
            for i, buy in enumerate(self.buys):
                if (current_price / buy['price']) - 1 > buy['yield_value']:
                    buys_ready[i] = buy
        return buys_ready


