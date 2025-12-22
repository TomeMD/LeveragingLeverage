import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import ipywidgets as widgets

from filter_data import filter_dataset_by_period, filter_dataset_by_days


# ------------------------------------------------------------------------------------------------------------------
# AUXILIAR FUNCTIONS
# ------------------------------------------------------------------------------------------------------------------
def make_range_slider_from_df_column(df, column):
    if column == "Days":
        max_day = df["Days"].max()
        return widgets.IntRangeSlider(
            value=(0, max_day), 
            min=0, 
            max=max_day, 
            step=1,
            description='Days', 
            readout=True, 
            readout_format='d',
            continuous_update=False, 
            layout={"width": "100%", "height": "80px"}
        )
    if column == "Date":
        dates = df['Date'].astype(str)
        unique_sorted = sorted(set(dates))
        return widgets.SelectionRangeSlider(
            options=unique_sorted,
            index=(0, len(unique_sorted)-1),
            description="Dates Range",
            orientation="horizontal",
            continuous_update=False,
            layout={"width": "100%", "height": "80px"}
        )
    raise ValueError(f"Column '{column}' not supported to create range slider")

# ------------------------------------------------------------------------------------------------------------------
# PLOT DATA
# ------------------------------------------------------------------------------------------------------------------
def plot_dataset(df):
    plt.figure()
    ax = plt.gca()
    ax.plot(df['Date'], df['Adj Close'])

    # Format dates properly to avoid overlaping in short periods
    locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    plt.tight_layout()
    plt.show()


def plot_dataset_period(dataset, range_dates):
    start, end = range_dates
    plot_dataset(filter_dataset_by_period(dataset, start, end))
    

def plot_dataset_interactive(dataset, column="Date"):
    range_slider = make_range_slider_from_df_column(dataset, column)
    def _plot(range_dates):
        start, end = range_dates
        if column == "Date":
            plot_dataset(filter_dataset_by_period(dataset, start, end))
        if column == "Days":
            plot_dataset(filter_dataset_by_days(dataset, start, end))
    return widgets.interact(_plot, range_dates=range_slider)