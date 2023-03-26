from datetime import datetime
import pandas as pd


def create_month_range(year_month_start: str, year_month_end: str = None) -> list:
    """
    Function that creates a month interval range
    :param year_month_start: '%Y-%m' (ex: 2021-07)
    :param year_month_end: '%Y-%m' (ex: 2023-01)
    :return: list with year-month elements
    """

    # if year_month_end is None:
    #     year_month_end = f'{datetime.now().year}-{datetime.now().month if datetime.now().month > 9 else f"0{datetime.now().month}"}'

    if year_month_end is None:
        year_month_end = datetime.now().strftime("%Y-%m")

    month_list = pd.date_range(
        f'{year_month_start}-01',
        f'{year_month_end}-01',
        freq='MS'
    ).tolist()

    return [datetime.strftime(t, '%Y-%m') for t in month_list]
