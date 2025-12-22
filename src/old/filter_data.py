from datetime import datetime

# ------------------------------------------------------------------------------------------------------------------
# FILTER DATA
# ------------------------------------------------------------------------------------------------------------------
def filter_dataset_by_period(df, period_start, period_end):
    start = datetime.strptime(period_start, "%Y-%m-%d")
    end = datetime.strptime(period_end, "%Y-%m-%d")
    return df[df['Date'].between(start, end)]

def filter_dataset_by_days(df, days_start, days_end):
    return df[df['Days'].between(days_start, days_end)]