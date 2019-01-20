# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""p2p_helper contains some helper functions for easyP2P."""

import calendar
from datetime import datetime, date, timedelta
from typing import List, Tuple


def get_calendar_clicks(
        target_date: datetime.date, start_date: datetime.date) -> int:
    """
    Get number of calendar clicks necessary to get from start to target month.

    This function will determine how many months in the
    past/future the target date is compared to a given
    start date. Positive numbers mean months into the
    future, negative numbers months into the past.

    Args:
        target_date (datetime.date): Target date.
        start_date (datetime.date): Start date.

    Returns:
        int: number of months between start and
            target date.

    """
    if target_date.year != start_date.year:
        clicks = 12 * (target_date.year - start_date.year)
    else:
        clicks = 0

    if target_date.month != start_date.month:
        clicks += target_date.month - start_date.month

    return clicks

def get_list_of_months(
        start_date: datetime.date,
        end_date: datetime.date) -> List[Tuple[datetime.date, datetime.date]]:
    """
    Get list of months between (including) start and end date.

    Args:
        start_date (datetime.date): start date
        end_date (datetime.date): end_date

    Returns:
        list[tuple[datetime.date, datetime.date]]: List of tuples
            (start_of_month, end_of_month)
    """
    months = []
    current_date = start_date
    while current_date < end_date:
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

    Returns:
        str: two-digit month number padded with 0

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

    Returns:
        str: month short name

    """
    # Only German locale is used so far
    map_nbr_to_short_month = {
        '01': 'Jan', '02': 'Feb', '03': 'Mrz', '04': 'Apr', '05': 'Mai',
        '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Okt',
        '11': 'Nov', '12': 'Dez'}

    return map_nbr_to_short_month[nbr]
