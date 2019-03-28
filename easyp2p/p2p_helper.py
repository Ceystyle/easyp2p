# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_helper contains some helper functions/classes for easyP2P.

Functions:

* get_calendar_clicks: get number of calendar clicks necessary to get from \
    provided start to target month.
* get_df_from_file: read a pandas DataFrame from given input file.
* get_list_of_months: returns a list of all months between provided start and \
    end date.
* short_month_to_nbr: translates month short name to number.
* nbr_to_short_month: translates number to month short name.

Classes:

* one_of_many_expected_conditions_true: expected condition for the Selenium \
    webdriver.

"""

import calendar
from datetime import date, timedelta
from pathlib import Path
import os
from typing import Callable, List, Tuple

from selenium import webdriver
import pandas as pd


def get_calendar_clicks(
        target_date: date, start_date: date) -> int:
    """
    Get number of calendar clicks necessary to get from start to target month.

    This function will determine how many months in the
    past/future the target date is compared to a given
    start date. Positive numbers mean months into the
    future, negative numbers months into the past.

    Args:
        target_date: Target date.
        start_date: Start date.

    Returns:
        Number of months between start and target date.

    """
    if target_date.year != start_date.year:
        clicks = 12 * (target_date.year - start_date.year)
    else:
        clicks = 0

    if target_date.month != start_date.month:
        clicks += target_date.month - start_date.month

    return clicks


def get_df_from_file(input_file: str) -> pd.DataFrame:
    """
    Read a pandas.DataFrame from input_file.

    Args:
        input_file: file name including path

    Returns:
        pandas.DataFrame: DataFrame which was read from the file

    Raises:
        RuntimeError: If input_file does not exist, cannot be read or if the \
            file format is neither csv or xlsx

    """

    file_format = Path(input_file).suffix

    try:
        if file_format == '.csv':
            df = pd.read_csv(input_file)
        elif file_format in ('.xlsx', '.xls'):
            df = pd.read_excel(input_file)
        else:
            raise RuntimeError(
                'Unbekanntes Dateiformat beim Import: ', input_file)
    except FileNotFoundError:
        raise RuntimeError(
            '{0} konnte nicht gefunden werden!'.format(input_file))

    return df


def get_list_of_months(date_range: Tuple[date, date]) \
        -> List[Tuple[date, date]]:
    """
    Get list of months between (including) start and end date.

    Args:
        date_range: Tuple (start_date, end_date)

    Returns:
        List of tuples (start_of_month, end_of_month) for all months between \
        start and end date.

    """
    months = []
    current_date = date_range[0]
    while current_date < date_range[1]:
        start_of_month = date(current_date.year, current_date.month, 1)
        end_of_month = date(
            current_date.year, current_date.month, calendar.monthrange(
                current_date.year, current_date.month)[1])
        months.append((start_of_month, end_of_month))
        current_date += timedelta(days=31)

    return months


def short_month_to_nbr(short_name: str) -> str:
    """
    Helper method for translating month short names to numbers.

    Args:
        short_name: Month short name

    Returns:
        Two-digit month number padded with 0

    """
    map_short_month_to_nbr = {
        'Jan': '01', 'Feb': '02', 'Mrz': '03', 'Mar': '03',
        'Apr': '04', 'Mai': '05', 'May': '05', 'Jun': '06', 'Jul': '07',
        'Aug': '08', 'Sep': '09', 'Okt': '10', 'Oct': '10', 'Nov': '11',
        'Dez': '12', 'Dec': '12'}

    return map_short_month_to_nbr[short_name]


def nbr_to_short_month(nbr: str) -> str:
    """
    Helper method for translating numbers to month short names.

    Args:
        nbr: Number of month with or without a leading zero

    Returns:
        Month short name

    """
    # Only German locale is used so far
    map_nbr_to_short_month = {
        '1': 'Jan', '01': 'Jan', '2': 'Feb', '02': 'Feb',
        '3': 'Mrz', '03': 'Mrz', '4': 'Apr', '04': 'Apr',
        '5': 'Mai', '05': 'Mai', '6': 'Jun', '06': 'Jun',
        '7': 'Jul', '07': 'Jul', '8': 'Aug', '08': 'Aug',
        '9': 'Sep', '09': 'Sep', '10': 'Okt', '11': 'Nov', '12': 'Dez'}

    return map_nbr_to_short_month[nbr]


def set_statement_file_name(
        platform_name: str, dl_dir: str, suffix: str,
        date_range: Tuple[date, date], statement_file: str = None) -> str:
    """
    Helper method for setting the account statement download file name.

    Default file name will be 'platform name'_statement-'start_date'-
    'end-date.suffix. statement_file can be used to override the default.

    Args:
        platform_name: Name of the platform
        dl_dir: path of the download directory
        suffix: suffix of the file name (csv, xlsx or xls)
        date_range: date range for which the account statement will be
            generated

    Keyword Args:
        statement_file: if not None this will override the default file name

    Returns:
        File name including path where the paltform account statement should
        be saved

    """
    if statement_file is not None:
        return statement_file
    else:
        return os.path.join(
            dl_dir, '{0}_statement_{1}-{2}.{3}'.format(
                platform_name.lower(), date_range[0].strftime('%Y%m%d'),
                date_range[1].strftime('%Y%m%d'), suffix))


class one_of_many_expected_conditions_true():
    """
    An expectation for checking if (at least) one of several provided expected
    conditions for the Selenium webdriver is true.
    """
    def __init__(self, conditions: List[Callable[[webdriver.Chrome], bool]]) \
            -> None:
        """
        Initialize class.

        Args:
            conditions: List of all conditions which should be checked.

        """
        self.conditions = conditions

    def __call__(self, driver: webdriver.Chrome) -> bool:
        """
        Caller for class.

        Args:
            driver: Selenium webdriver

        Returns:
            True if at least one of the conditions is true, False otherwise.

        """
        for condition in self.conditions:
            try:
                if condition(driver):
                    return True
            except:
                pass
        return False
