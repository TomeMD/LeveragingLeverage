import os
import streamlit as st
import numpy as np

from src.backtest.strategy.Asset import Asset

ENTRY_THRESHOLDS = {
    # x2
    -0.10: (0.05, "x2"),
    -0.15: (0.12, "x2"),
    -0.20: (0.20, "x2"),
    # x3
    -0.25: (0.10, "x3"),
    -0.30: (0.20, "x3"),
    -0.35: (0.30, "x3"),
    -0.40: (0.40, "x3"),
    -0.50: (0.50, "x3"),
    -0.60: (0.60, "x3"),
    -0.70: (0.70, "x3"),
    -0.80: (0.80, "x3")
}


MAX_PCTS = {"x2": 0.20, "x3": 0.80}


def check_current_dd(total_eur, dd, entry_thresholds):
    # Get the percentage of total capital that should be invested in each type of asset for current drawdown
    buy_amounts = {}
    for pct, (buy_pct, buy_type) in entry_thresholds.items():
        if pct > dd:
            max_eur = MAX_PCTS[buy_type] * total_eur
            buy_amounts[buy_type] = min(max(buy_amounts.get(buy_type, 0), buy_pct * total_eur), max_eur)
        else:
            break

    return buy_amounts


def get_prev_factor(lev_factor):
    # WARNING! Workaround to work only with x2 and x3
    if lev_factor == "x3":
        return "x2"
    return None


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


def backtest(df, df_x2, df_x3, total_eur, interactive=False):
    if not os.path.exists("logs") or not os.path.isdir("logs"):
        os.mkdir("logs")
    log_path = f"logs/thresholds.log"

    days = df['Days'].to_numpy(dtype=np.int64)
    prices, ath, dd, dmax = compute_drawdowns(df)
    prices_x2, ath_x2, dd_x2, dmax_x2 = compute_drawdowns(df_x2)
    prices_x3, ath_x3, dd_x3, dmax_x3 = compute_drawdowns(df_x3)
    wallet = {
        "earnings": 0.0,
        "cash": total_eur,
        "x2": Asset("S&P500 x2", prices_x2, total_eur * MAX_PCTS["x2"], log_path),
        "x3": Asset("S&P500 x3", prices_x3, total_eur * MAX_PCTS["x3"], log_path)
    }
    buys_tracker = []
    rotate_tracker = []
    sells_tracker = []

    # Mantener fijo invested_eur y total_eur
    # Cuando se vende invested_eur se reduce y como mucho puede llegar a 0, lo sobrante empieza a ir a earnings
    # A mayores tenemos invested_value para trackear perdidas o ganancias latentes

    # Compute prices, ath, drawdowns and max drawdowns along the whole dataset
    for t in range(len(prices)):
        current_price = {"x1": prices[t], "x2": prices_x2[t], "x3": prices_x3[t]}
        current_dd = dd[t]
        current_dmax = dmax[t]
        current_day = days[t]

        if interactive:
            st.info(f"@iteration {t}: @price: {current_price['x1']} @dd: {current_dd} @dmax: {current_dmax}")
            st.info(f"@iteration {t}: @cash {wallet['cash']}: @earnings: {wallet['earnings']}")

        target_invested = check_current_dd(total_eur, current_dd, ENTRY_THRESHOLDS)

        # BUY OR ROTATE
        for lev_factor, target_amount in target_invested.items():
            asset = wallet.get(lev_factor, None)
            if not asset:
                print(f"Trying to invest in a non-existent asset: {lev_factor} (indexed by leverage factor)")
                continue

            invested_amount = asset.get_invested_eur()
            if target_amount > invested_amount:
                amount_to_invest = target_amount - invested_amount
                if interactive:
                    print(f"BUY IN PROCESS @amount {amount_to_invest}")
                    _ = input("Enter to see result: ")

                # FIRST, TRY TO ROTATE
                prev_factor = get_prev_factor(lev_factor)
                if prev_factor:
                    prev_asset = wallet.get(prev_factor, None)
                    extra_cash = 0.0 if not prev_asset else prev_asset.get_extra_cash(t)
                    if extra_cash > 0.0:
                        amount_to_rotate = min(amount_to_invest, extra_cash)
                        prev_asset.rotate_down_sell(asset.get_ticker(), amount_to_rotate, t)
                        asset.rotate_buy(prev_asset.get_ticker(), amount_to_rotate, t)
                        amount_to_invest -= amount_to_rotate
                        rotate_tracker.append((f"{prev_factor} to {lev_factor}", current_day))

                # BUY WITH CASH
                if amount_to_invest > 0.0:
                    amount_to_invest = min(amount_to_invest, wallet["cash"])
                    if amount_to_invest > 0.0:
                        asset.buy(amount_to_invest, t)
                        wallet["cash"] -= amount_to_invest
                        buys_tracker.append((lev_factor, current_day))


        # SELL OR ROTATE
        for lev_factor in ["x2", "x3"]:
            asset = wallet.get(lev_factor, None)
            buys_ready = asset.check_buys_yields(t)
            for i, buy in buys_ready.items():
                if interactive:
                    print(f"SELL IN PROCESS @amount {buy['amount']}")
                    _ = input("Enter to see result: ")

                prev_factor = get_prev_factor(lev_factor)
                if prev_factor:
                    prev_asset = wallet.get(prev_factor, None)
                    amount = asset.sell_by_index(i, t)
                    prev_asset.rotate_buy(asset.get_ticker(), amount, t)
                    rotate_tracker.append((f"{lev_factor} to {prev_factor}", current_day))

                else:
                    amount = asset.sell_by_index(i, t)
                    if wallet["cash"] + amount > total_eur:
                        wallet["earnings"] += (wallet["cash"] + amount - total_eur)
                        wallet["cash"] = total_eur
                    else:
                        wallet["cash"] += amount
                    sells_tracker.append((lev_factor, current_day))

        # SI VENDO UN X3 -> SI EXISTE UN PREV_FACTOR
        # ROTAR AMOUNT A X2 -> ROTAR A PREV_FACTOR
        # asset.sell_by_index(buy, i)
        # sell by index debe:
        # -> Devolver el amount ganado
        # -> Eliminar compra de self.buys -> del self.buys[i]
        # -> Reducir self.invested_eur, self.invested_qty, self.invested_value
        # Invertir amount ganado en x2
        # prev_asset.rotate_buy()


        # Si lev_factor = x2
        # asset.sell_by_index(buy, i)
        # El dinero obtenido se ira a cash, si el cash, sobrepasa 10.000, se ira a earnings
    wallet["buys_tracker"] = buys_tracker
    wallet["rotate_tracker"] = rotate_tracker
    wallet["sells_tracker"] = sells_tracker

    return wallet

    #return trades

    #Capital inicial - 10000
    #Valor inicial - 100

    #Valor baja a 90 (-10%) -> Compro 300€ (3% * 10000)

    #Valor sube a 95 (rec 50%) -> Vendo 10% de 10.000 * 95/90 =

    #Formula para calcular la subida que supone un % de recuperacion sobre dmax?

    #Si recupero el 50% de un -40%, caida=de -40% a -20%
    #100 -> 60 -> 80 = 80/60 - 1 =  = 33,33%
    #432 -> 259,2 -> 345,6 = 345,6/259,2 - 1 =  = 33,33%
    #
    #(1 - 0.2)/(1 - 0.4) = (1 - dd)/(1 - dmax)