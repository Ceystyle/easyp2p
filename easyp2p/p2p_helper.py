# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_helper contains some helper functions for easyp2p.

"""
from PyQt5.QtCore import QCoreApplication
translate = QCoreApplication.translate


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
    map_nbr_to_short_month = {
        '1': translate('MainWindow', 'Jan'),
        '01': translate('MainWindow', 'Jan'),
        '2': translate('MainWindow', 'Feb'),
        '02': translate('MainWindow', 'Feb'),
        '3': translate('MainWindow', 'Mar'),
        '03': translate('MainWindow', 'Mar'),
        '4': translate('MainWindow', 'Apr'),
        '04': translate('MainWindow', 'Apr'),
        '5': translate('MainWindow', 'May'),
        '05': translate('MainWindow', 'May'),
        '6': translate('MainWindow', 'Jun'),
        '06': translate('MainWindow', 'Jun'),
        '7': translate('MainWindow', 'Jul'),
        '07': translate('MainWindow', 'Jul'),
        '8': translate('MainWindow', 'Aug'),
        '08': translate('MainWindow', 'Aug'),
        '9': translate('MainWindow', 'Sep'),
        '09': translate('MainWindow', 'Sep'),
        '10': translate('MainWindow', 'Oct'),
        '11': translate('MainWindow', 'Nov'),
        '12': translate('MainWindow', 'Dec'),
    }

    return map_nbr_to_short_month[nbr]
