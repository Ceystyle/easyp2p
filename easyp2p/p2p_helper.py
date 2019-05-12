# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_helper contains some helper functions for easyp2p.

"""

from pathlib import Path

import pandas as pd


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
