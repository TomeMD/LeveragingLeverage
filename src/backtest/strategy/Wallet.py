

class Wallet:

    def __init__(self, initial_cash):
        self.cash = initial_cash
        self.assets = {}
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

    def invested_amount(self, key):
        return self.assets[key].get_invested_eur()

    def invested_value(self, key):
        return self.assets[key].get_invested_value()

    def total_invested(self):
        return sum(a.get_invested_eur() for a in self.assets.values())

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

    # ---------- Trackers ----------

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
            "buy_tracker": self.buy_tracker,
            "rotate_tracker": self.rotate_tracker,
            "sell_tracker": self.sell_tracker,
        }
