# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_helper contains some helper functions for easyp2p.

"""

import calendar
from datetime import date, timedelta
import os
from pathlib import Path
from typing import List, Optional, Tuple

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
    Get list of months between (and including) start and end date.

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
        days_in_month = calendar.monthrange(
            current_date.year, current_date.month)[1]
        end_of_month = date(
            current_date.year, current_date.month, days_in_month)
        months.append((start_of_month, end_of_month))
        current_date += timedelta(days=days_in_month)

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


def create_statement_location(
        name: str, date_range: Tuple[date, date], suffix: str,
        statement_file: Optional[str] = None) -> str:
    """
    Helper function for creating the account statement download location.

    Default file name will be 'platform name'_statement-'start_date'-
    'end-date'.suffix. statement_file can be used to override the default.
    This is mainly useful for the tests.

    Args:
        name: Name of the P2P platform
        date_range: Date range (start_date, end_date) for which the account
            statement must be generated
        suffix: Suffix of the statement file
        statement_file: If not None this will override the default file
            name. Default is None.

    Returns:
        File name including path where the platform account statement
        should be saved

    """
    if statement_file is None:
        dl_dir = os.path.join(Path.home(), '.easyp2p', name.lower())
        statement_file = os.path.join(
            dl_dir, '{0}_statement_{1}-{2}.{3}'.format(
                name.lower(), date_range[0].strftime('%Y%m%d'),
                date_range[1].strftime('%Y%m%d'), suffix))
    else:
        dl_dir = os.path.dirname(statement_file)

    # Create download directory if it doesn't exist yet
    if not os.path.isdir(dl_dir):
        os.makedirs(dl_dir)

    return statement_file
