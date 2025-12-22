import os

class Asset:

    def __init__(self, ticker, prices, max_eur, log_file):
        self.ticker = ticker
        self.prices = prices
        self.max_eur = max_eur
        if os.path.exists(log_file):
            os.remove(log_file)
        self.log_file = log_file
        self.invested_eur = 0
        self.invested_qty = 0
        self.invested_value = 0
        self.buys = []

    def __create_buy(self, t, amount, qty):
        return {
            "index": t,
            "ticker": self.ticker,
            "price": self.prices[t],
            "amount": amount,
            "qty": qty,
            "yield_target": 0.5 if "x2" in self.ticker else 1.0,
            "invested_eur": self.invested_eur,
            "pending_until_max": max(self.max_eur - self.invested_eur, 0)
        }

    def __log_and_print(self, msg):
        with open(self.log_file, "a") as f:
            f.write(f"{msg}\n")
        print(msg)

    def __print_buy(self, buy_item):
        self.__log_and_print("************************ BUY ************************")
        self.__log_and_print(f"{'Ticker':<30}: {buy_item['ticker']:>10}")
        self.__log_and_print(f"{'Buy time':<30}: {buy_item['index']:>10}")
        self.__log_and_print(f"{'Price':<30}: {buy_item['price']:>10.2f}")
        self.__log_and_print(f"{'Amount':<30}: {buy_item['amount']:>10.2f}")
        self.__log_and_print(f"{'Quantity':<30}: {buy_item['qty']:>10.2f}")
        self.__log_and_print(f"{'Yield target':<30}: {buy_item['yield_target']:>10.2f}")
        self.__log_and_print(f"{'Invested EUR (after buy)':<30}: {self.invested_eur:>10.2f}")
        self.__log_and_print(f"{'Pending until max':<30}: {buy_item['pending_until_max']:>10.2f}")
        self.__log_and_print("*****************************************************")

    def __print_sell(self, buy_item, sell_time, sell_price, final_amount, final_yield):
        self.__log_and_print("************************ SELL ************************")
        self.__log_and_print(f"{'Ticker':<30}: {buy_item['ticker']:>10}")
        self.__log_and_print(f"{'Buy time':<30}: {buy_item['index']:>10}")
        self.__log_and_print(f"{'Buy Price':<30}: {buy_item['price']:>10.2f}")
        self.__log_and_print(f"{'Sell time':<30}: {sell_time:>10}")
        self.__log_and_print(f"{'Sell price':<30}: {sell_price:>10.2f}")
        self.__log_and_print(f"{'Initial amount':<30}: {buy_item['amount']:>10.2f}")
        self.__log_and_print(f"{'Final amount':<30}: {final_amount:>10.2f}")
        self.__log_and_print(f"{'Yield target':<30}: {buy_item['yield_target']:>10.2f}")
        self.__log_and_print(f"{'Final yield':<30}: {final_yield:>10.2f}")
        self.__log_and_print(f"{'Invested EUR (after sell)':<30}: {self.invested_eur:>10.2f}")
        self.__log_and_print("*****************************************************")

    def __print_partial_sell(self, buy_item, sell_time, sell_price, sell_qty, final_amount, final_yield):
        self.__log_and_print("******************** PARTIAL SELL ********************")
        self.__log_and_print(f"{'Ticker':<30}: {buy_item['ticker']:>10}")
        self.__log_and_print(f"{'Buy time':<30}: {buy_item['index']:>10}")
        self.__log_and_print(f"{'Buy Price':<30}: {buy_item['price']:>10.2f}")
        self.__log_and_print(f"{'Sell time':<30}: {sell_time:>10}")
        self.__log_and_print(f"{'Sell price':<30}: {sell_price:>10.2f}")
        self.__log_and_print(f"{'Initial amount':<30}: {buy_item['amount']:>10.2f}")
        self.__log_and_print(f"{'Sold amount':<30}: {(sell_qty*buy_item['price']):>10.2f}")
        self.__log_and_print(f"{'Final amount':<30}: {final_amount:>10.2f}")
        self.__log_and_print(f"{'Yield target':<30}: {buy_item['yield_target']:>10.2f}")
        self.__log_and_print(f"{'Final yield':<30}: {final_yield:>10.2f}")
        self.__log_and_print(f"{'Invested EUR (after sell)':<30}: {self.invested_eur:>10.2f}")
        self.__log_and_print("*****************************************************")

    def get_ticker(self):
        return self.ticker

    def get_invested_eur(self):
        return self.invested_eur

    def get_buys(self):
        return self.buys

    def get_extra_cash(self, t):
        self.invested_value = self.invested_qty * self.prices[t]
        return max(self.invested_value - self.max_eur, 0)

    def __add_buy(self, amount_eur, t):
        # Compute invested qty
        # TODO: Compute real amount because we cannot invest fractional amounts
        qty = amount_eur / self.prices[t]

        # Update cummulative amounts
        self.invested_eur += amount_eur
        self.invested_qty += qty
        self.invested_value = self.prices[t] * self.invested_qty

        # Create and add buy
        self.buys.append(self.__create_buy(t, amount_eur, qty))

    # Buy shares using cash
    def buy(self, amount_eur, t):
        # Check investment upper limit is not surpassed
        if self.invested_eur + amount_eur > self.max_eur:
            raise ValueError(f"Trying to buy more than {self.max_eur} of {self.ticker} using cash. Aborting...")

        # Add buy
        self.__add_buy(amount_eur, t)

        # Print buy info
        self.__log_and_print(f"Using cash to buy {amount_eur}€ of {self.ticker}")
        self.__print_buy(self.buys[-1])

    # Buy shares by rotating from higher leverage factors
    def rotate_buy(self, from_ticker, amount_eur, t):
        # Add buy
        self.__add_buy(amount_eur, t)

        # Print buy info
        self.__log_and_print(f"Rotating {amount_eur}€ from {from_ticker} to {self.ticker}")
        self.__print_buy(self.buys[-1])

    # Sell shares to rotate to higher leverage factors
    def rotate_down_sell(self, to_ticker, amount_eur, t):
        if amount_eur > self.invested_value:
            raise ValueError(f"Trying to rotate {amount_eur} from {self.ticker} to {to_ticker} but current invested value is lower: {self.invested_value}")
        pending_amount = amount_eur
        current_price = self.prices[t]
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

            self.__log_and_print(f"Rotating {sell_amount}€ from {self.ticker} to {to_ticker}")
            if sell_amount >= buy_value:
                self.__print_sell(buy_item, t, current_price, sell_amount, final_yield)
                del self.buys[0]
            else:
                self.__log_and_print(f"Only a part of the buy will be sold because buy value ({buy_value}) is higher than amount to rotate {sell_amount}")
                self.__print_partial_sell(buy_item, t, current_price, sell_qty, sell_amount, final_yield)
                self.buys[0]['qty'] -= sell_qty
                self.buys[0]['amount'] = self.buys[0]['qty'] * self.buys[0]['price']

            pending_amount -= sell_amount

    def sell_by_index(self, idx, t):
        buy_item = self.buys[idx]
        qty = buy_item['qty']
        buy_price = buy_item['price']
        current_price = self.prices[t]
        target_yield = buy_item['yield_target']
        final_yield = (current_price / buy_price) - 1
        initial_amount = buy_item['amount']
        final_amount = current_price * qty
        buy_time = buy_item['index']

        self.invested_eur -= initial_amount
        self.invested_qty -= qty
        self.invested_value = current_price * self.invested_qty

        self.__log_and_print(f"Selling {initial_amount}€ of {self.ticker} that has reached its yield target")
        self.__print_sell(buy_item, t, current_price, final_amount, final_yield)

        del self.buys[idx]

        return final_amount

    def check_buys_yields(self, t):
        buys_ready = {}
        current_price = self.prices[t]
        for i, buy in enumerate(self.buys):
            if (current_price / buy['price']) - 1 > buy['yield_target']:
                buys_ready[i] = buy
        return buys_ready


