# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Bondora statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
import locale
from typing import Tuple

import pandas as pd
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import p2p_helper
from p2p_parser import P2PParser
from p2p_platform import P2PPlatform


def download_statement(
        date_range: Tuple[date, date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Bondora account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Bondora

    """
    # TODO: check if the input variables are sane, also for the other
    # open_selenium_* functions
    urls = {
        'login': 'https://www.bondora.com/de/login',
        'logout': 'https://www.bondora.com/de/authorize/logout',
        'statement': 'https://www.bondora.com/de/cashflow'}
    xpaths = {
        'no_payments': '/html/body/div[1]/div/div/div/div[3]/div',
        'search_btn': ('//*[@id="page-content-wrapper"]/div/div/div[1]/form/'
                       'div[3]/button'),
        'start_date': ('/html/body/div[1]/div/div/div/div[3]/div/table/tbody/'
                       'tr[2]/td[1]/a')}

    with P2PPlatform('Bondora', urls, EC.title_contains('Einloggen')) \
        as bondora:

        driver = bondora.driver

        # _no_payments is set True if there were no cashflows in date_range
        _no_payments = False

        bondora.log_into_page(
            'Email', 'Password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Cashflow')))

        bondora.open_account_statement_page('Cashflow', (By.ID, 'StartYear'))

        # Get the default values for start and end date
        start_year = Select(
            driver.find_element_by_id('StartYear')).first_selected_option.text
        start_month = Select(
            driver.find_element_by_id('StartMonth')).first_selected_option.text
        end_year = Select(
            driver.find_element_by_id('EndYear')).first_selected_option.text
        end_month = Select(
            driver.find_element_by_id('EndMonth')).first_selected_option.text

        # Change the date values to the given start and end dates
        if start_year != date_range[0].year:
            select = Select(driver.find_element_by_id('StartYear'))
            select.select_by_visible_text(str(date_range[0].year))

        if (p2p_helper.short_month_to_nbr(start_month)
                != date_range[0].strftime('%m')):
            select = Select(driver.find_element_by_id('StartMonth'))
            select.select_by_visible_text(p2p_helper.nbr_to_short_month(
                date_range[0].strftime('%m')))

        if end_year != date_range[1].year:
            select = Select(driver.find_element_by_id('EndYear'))
            select.select_by_visible_text(str(date_range[1].year))

        if p2p_helper.short_month_to_nbr(end_month) \
                != date_range[1].strftime('%m'):
            select = Select(driver.find_element_by_id('EndMonth'))
            select.select_by_visible_text(p2p_helper.nbr_to_short_month(
                date_range[1].strftime('%m')))

        # Start the account statement generation
        driver.find_element_by_xpath(xpaths['search_btn']).click()

        # Wait until statement generation is finished. If the statement cannot
        # be found a TimeoutException is raised. That can happen in case of
        # errors or when there were no cashflows in the requested period.
        try:
            bondora.wdwait(
                EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['start_date']),
                    '{0} {1}'.format(
                        date_range[0].strftime('%b'), date_range[0].year)))
        except TimeoutException as err:
            if 'Keine Zahlungen gefunden' in \
                    driver.find_element_by_xpath(xpaths['no_payments']).text:
                _no_payments = True
            else:
                raise TimeoutException(err)

        if _no_payments:
            df = pd.DataFrame()
        else:
            # Scrape cashflows from the web site and write them to csv file
            cashflow_table = driver.find_element_by_id('cashflow-content')
            df = pd.read_html(
                cashflow_table.get_attribute("innerHTML"), index_col=0,
                thousands='.', decimal=',')[0]

        df.to_csv('p2p_downloads/bondora_statement.csv')


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/bondora_statement.csv') \
            -> Tuple[pd.DataFrame, str]:
    """
    Parser for Bondora.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Bondora web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Bondora', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # The first and last row only contain a summary
    parser.df = parser.df[1:-1]

    # Bondora uses month short names, thus we need to make sure the right
    # locale is used
    # TODO: make sure locale is installed or find better way to fix this
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

    # Fix the number format
    parser.df.set_index('Zeitraum', inplace=True)
    parser.df.replace({r'\.': '', ',': '.', '€': ''}, inplace=True, regex=True)
    parser.df = parser.df.astype('float64')
    parser.df.reset_index(inplace=True)

    # Calculate defaulted payments
    parser.df[parser.DEFAULTS] = (
        parser.df['Erhaltener Kapitalbetrag - gesamt']
        - parser.df['Geplanter Kapitalbetrag - gesamt'])

    # Define mapping between Bondora and easyP2P column names
    rename_columns = {
        'Eingesetztes Kapital (netto)': parser.INCOMING_PAYMENT,
        'Erhaltener Kapitalbetrag - gesamt': parser.REDEMPTION_PAYMENT,
        'Erhaltene Zinsen - gesamt': parser.INTEREST_PAYMENT,
        'Investitionen (netto)': parser.INVESTMENT_PAYMENT,
        'Zeitraum': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%b %Y', rename_columns=rename_columns)

    return (parser.df, unknown_cf_types)
