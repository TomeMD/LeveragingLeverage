

class Wallet:

    def __init__(self, initial_cash):
        self.cash = initial_cash
        self.assets = {}
        self.fees_paid = 0.0

        # Trackers
        self.debt_cost_tracker = 0.0  # Used when wallet cash comes from a debt
        self.debt_time_tracker = 0
        self.tuw_tracker = 0
        self.buy_tracker = []
        self.rotate_tracker = []
        self.sell_tracker = []

    # ---------- Asset management ----------

    def add_asset(self, key, asset):
        self.assets[key] = asset

    def get_asset(self, key):
        if key not in self.assets:
            raise KeyError(f"Trying to get a non-existent asset: {key} (indexed by leverage factor)")
        return self.assets[key]

    def get_invested_amount(self, asset):
        return self.assets[asset].get_invested_eur()

    def get_invested_value(self, asset):
        return self.assets[asset].get_invested_value()

    def get_assets_invested(self):
        return sum(a.get_invested_eur() for a in self.assets.values())

    def get_assets_value(self):
        return sum(a.get_invested_value() for a in self.assets.values())

    def get_total_value(self):
        return self.cash + self.get_assets_value()

    # ---------- Cash management ----------

    def can_spend(self, amount):
        return self.cash >= amount

    def spend(self, amount):
        if amount > self.cash:
            raise ValueError("Not enough cash")
        self.cash -= amount

    def receive(self, amount):
        self.cash += amount

    def fill(self, amount):
        self.cash = amount

    def pay_fees(self, amount):
        self.fees_paid += amount

    # ---------- Trackers ----------

    def track_debt_cost(self, amount):
        self.debt_cost_tracker += amount

    def track_debt_time(self, days):
        self.debt_time_tracker += days

    def track_time_under_water(self, days):
        self.tuw_tracker += days

    def track_buy(self, name, day):
        self.buy_tracker.append((name, day))

    def track_rotate(self, name, day):
        self.rotate_tracker.append((name, day))

    def track_sell(self, name, day):
        self.sell_tracker.append((name, day))

    # ---------- Export ----------

    def to_dict(self):
        return {
            "cash": self.cash,
            **self.assets,
            "assets": list(self.assets.keys()),
            "fees_paid": self.fees_paid,
            "debt_cost": self.debt_cost_tracker,
            "debt_time": self.debt_time_tracker,
            "tuw": self.tuw_tracker,
            "buy_tracker": self.buy_tracker,
            "rotate_tracker": self.rotate_tracker,
            "sell_tracker": self.sell_tracker,
        }
