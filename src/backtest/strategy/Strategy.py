import numpy as np

class Strategy:

    """Base class for all strategies."""

    def __init__(self, name, initial_capital, input_dfs):
        self.name = name
        self.initial_capital = initial_capital
        self.input_dfs = input_dfs
        self.lev_factors = sorted(list(input_dfs.keys()))

    def set_initial_capital(self, value):
        if value < 0:
            raise ValueError(f"Trying to set an initial capital lower than 0 ({value}) for strategy {self.name}")
        self.initial_capital = value

    def get_prev_factor(self, lev_factor):
        return self.lev_factors[max(0, self.lev_factors.index(lev_factor) - 1)]

    @staticmethod
    def compute_drawdowns(df):
        price = df['Adj Close'].to_numpy(dtype=np.float64)
        ath = np.maximum.accumulate(price)

        # dd will have negative values or 0.0, which means this price is an ATH, as price/ATH - 1 = 0 only if price=ATH
        dd = price / ath - 1.0
        dd_df = df["Adj Close"].div(ath).sub(1.0)

        # Take values equal to 0 (ATH), that come from a previous non-zero value (drowdown), which means a recover drom a drodown
        # This df will contain True when we arrive an ATH from a previous dd
        val_is_zero = np.where(dd == 0.0, True, False)
        shifted_array = np.append(np.inf, dd[:-1])
        previous_val_not_zero = np.where(shifted_array != 0.0, True, False)
        new_ath = np.logical_and(val_is_zero, previous_val_not_zero)

        # Now we True values can be summed up accumulating the sum, then one True will mean first drop cycle, two True values second drop cycle,...
        # This way we have different cicle ids for each drop cycle
        cycle_id = np.cumsum(new_ath)

        # Group by drop cycle and get the max drop (min value) acumulating
        dmax = dd_df.groupby(cycle_id).cummin().to_numpy(dtype=np.float64)

        return price, ath, dd, dmax