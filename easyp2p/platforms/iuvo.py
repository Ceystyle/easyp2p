# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Iuvo statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import p2p_helper
from p2p_parser import P2PParser
from p2p_platform import P2PPlatform


def download_statement(
        date_range: Tuple[date, date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Iuvo account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Iuvo.

    """
    urls = {
        'login': 'https://www.iuvo-group.com/de/login/',
        'statement': 'https://www.iuvo-group.com/de/account-statement/'}
    xpaths = {
        'statement_check': ('//*[@id="P2PPlatform_cont"]/div/div[6]/div/div/'
                            'div/strong[3]')}

    with P2PPlatform(
            'Iuvo', urls, EC.element_to_be_clickable((By.ID, 'einloggen')),
            logout_locator=(By.ID, 'P2PPlatform_logout'),
            hover_locator=(By.LINK_TEXT, 'User name')) as iuvo:

        driver = iuvo.driver

        iuvo.log_into_page(
            'login', 'password', credentials,
            EC.element_to_be_clickable(
                (By.ID, 'P2PPlatform_btn_deposit_page_add_funds')))

        # Click away cookie policy, if present
        try:
            driver.find_element_by_id(
                'CybotCookiebotDialogBodyButtonAccept').click()
        except NoSuchElementException:
            pass

        iuvo.open_account_statement_page(
            'Kontoauszug', (By.ID, 'date_from'))

        # Since Dec 2018 Iuvo only provides aggregated cashflows
        # for the whole requested date range, no more detailed information
        # Workaround to get monthly data: create account statement for
        # each month in date range

        # Get all required monthly date ranges
        months = p2p_helper.get_list_of_months(date_range)

        # Initialize empty DataFrame. For each month the results will be
        # appended to df_result.
        df_result = pd.DataFrame()

        # Generate statement for each month and scrape it from the web site
        for month in months:
            check_txt = '{0} - {1}'.format(
                month[0].strftime('%Y-%m-%d'), month[1].strftime('%Y-%m-%d'))

            # Define conditions if account statement generation is successful:
            # The first condition will be true if there were cashflows in
            # date_range, the second condition will be true of there were none
            conditions = [
                EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['statement_check']), check_txt),
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'text-center'), 'Keine passenden Daten!')]

            iuvo.generate_statement_direct(
                (month[0], month[1]), (By.ID, 'date_from'), (By.ID, 'date_to'),
                '%Y-%m-%d',
                wait_until=p2p_helper.one_of_many_expected_conditions_true(
                    conditions),
                submit_btn_locator=(By.ID, 'account_statement_filters_btn'))

            try:
                # Read statement from page
                statement_table = driver.find_element_by_class_name(
                    'table-responsive')
            except NoSuchElementException:
                # Check if there were no cashflows in month
                if driver.find_element_by_class_name(
                        'text-center').text == 'Keine passenden Daten!':
                    continue

            # pd.read_html returns a list of one element
            df = pd.read_html(
                statement_table.get_attribute("innerHTML"), index_col=0)[0]

            # Transpose table to get the headers at the top
            df = df.T

            # Format date column
            df['Datum'] = month[0].strftime('%d.%m.%Y')
            df.set_index('Datum', inplace=True)

            # Append the result for this month to previous months' results
            df_result = df_result.append(df, sort=True)

        df_result.to_csv('p2p_downloads/iuvo_statement.csv')


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/iuvo_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Iuvo.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Iuvo web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Iuvo', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Temporarily make date column an index to avoid an error during type
    # conversion
    parser.df.set_index('Datum', inplace=True)
    parser.df = parser.df.astype('float64')
    parser.df.reset_index(inplace=True)

    # Both interest and redemption payments are each reported in two columns
    # by Iuvo (payments on/before planned payment date). For our purposes this
    # is not necessary, so we will add them again.
    parser.df[parser.INTEREST_PAYMENT] = 0
    parser.df[parser.REDEMPTION_PAYMENT] = 0
    interest_types = ['erhaltene Zinsen', 'vorfristige erhaltene Zinsen']
    for elem in interest_types:
        if elem in parser.df.columns:
            parser.df[parser.INTEREST_PAYMENT] += parser.df[elem]
            del parser.df[elem]

    redemption_types = [
        'erhaltener Grundbetrag', 'vorfristiger erhaltener Grundbetrag']
    for elem in redemption_types:
        if elem in parser.df.columns:
            parser.df[parser.REDEMPTION_PAYMENT] += parser.df[elem]
            del parser.df[elem]

    # Define mapping between Iuvo and easyP2P cashflow types and column
    # names
    rename_columns = {
        'Anfangsbestand': parser.START_BALANCE_NAME,
        'Endbestand': parser.END_BALANCE_NAME,
        'erhaltener Rückkaufgrundbetrag': parser.BUYBACK_PAYMENT,
        'erhaltene Verspätungsgebühren': parser.LATE_FEE_PAYMENT,
        'Investitionen auf dem Primärmarkt mit Autoinvest':
            parser.INVESTMENT_PAYMENT}

    unknown_cf_types = parser.parse_statement('%d.%m.%Y', rename_columns)

    return (parser.df, unknown_cf_types)
