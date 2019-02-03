# -*- coding: utf-8 -*-

"""
Module for parsing output files of P2P platforms and printing combined results.

    Each P2P platform has a unique format for presenting investment results.
    The purpose of this module is to provide parser methods to transform them
    into a single output format. The combined output is aggregated and
    written to an Excel file.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""
from datetime import date, datetime
import locale
from typing import List, Mapping, Optional, Sequence, Tuple

import pandas as pd
import p2p_helper

# Define all necessary payment types
INTEREST_PAYMENT = 'Zinszahlungen'
BUYBACK_INTEREST_PAYMENT = 'Zinszahlungen aus Rückkäufen'
BUYBACK_PAYMENT = 'Rückkäufe'
INVESTMENT_PAYMENT = 'Investitionen'
REDEMPTION_PAYMENT = 'Tilgungszahlungen'
LATE_FEE_PAYMENT = 'Verzugsgebühren'
INCOMING_PAYMENT = 'Einzahlungen'
OUTGOING_PAYMENT = 'Auszahlungen'
DEFAULTS = 'Ausfälle'
START_BALANCE_NAME = 'Startguthaben'
END_BALANCE_NAME = 'Endsaldo'
TOTAL_INCOME = 'Gesamteinnahmen'
DATE = 'Datum'
PLATFORM = 'Plattform'
CURRENCY = 'Währung'

# TARGET_COLUMNS are the columns which will be shown in the final result file
TARGET_COLUMNS = [
    DATE,
    PLATFORM,
    CURRENCY,
    START_BALANCE_NAME,
    END_BALANCE_NAME,
    TOTAL_INCOME,
    INTEREST_PAYMENT,
    INVESTMENT_PAYMENT,
    REDEMPTION_PAYMENT,
    BUYBACK_PAYMENT,
    BUYBACK_INTEREST_PAYMENT,
    LATE_FEE_PAYMENT,
    DEFAULTS,
]


class P2PParser:

    """
    P2P parser for transforming account statements into easyP2P format.

    Each P2P platform uses a unique format for their account statements. The
    purpose of P2PParser is to provide parser methods for transforming those
    files into a single unified easyP2P statement format.

    """

    # Define all necessary payment types
    INTEREST_PAYMENT = 'Zinszahlungen'
    BUYBACK_INTEREST_PAYMENT = 'Zinszahlungen aus Rückkäufen'
    BUYBACK_PAYMENT = 'Rückkäufe'
    INVESTMENT_PAYMENT = 'Investitionen'
    REDEMPTION_PAYMENT = 'Tilgungszahlungen'
    LATE_FEE_PAYMENT = 'Verzugsgebühren'
    INCOMING_PAYMENT = 'Einzahlungen'
    OUTGOING_PAYMENT = 'Auszahlungen'
    DEFAULTS = 'Ausfälle'
    START_BALANCE_NAME = 'Startguthaben'
    END_BALANCE_NAME = 'Endsaldo'
    TOTAL_INCOME = 'Gesamteinnahmen'

    # Define additional column names
    DATE = 'Datum'
    MONTH = 'Monat'
    PLATFORM = 'Plattform'
    CURRENCY = 'Währung'

    # TARGET_COLUMNS are the columns which will be shown in the final result
    # file
    TARGET_COLUMNS = [
        DATE,
        PLATFORM,
        CURRENCY,
        START_BALANCE_NAME,
        END_BALANCE_NAME,
        TOTAL_INCOME,
        INTEREST_PAYMENT,
        INVESTMENT_PAYMENT,
        REDEMPTION_PAYMENT,
        BUYBACK_PAYMENT,
        BUYBACK_INTEREST_PAYMENT,
        LATE_FEE_PAYMENT,
        DEFAULTS ]

    def __init__(
            self, platform: str, date_range: Tuple[date, date],
            input_file: str) -> None:
        """
        Constructor of P2PParser class.

        Args:
            platform (str): Name of the P2P platform
            date_range (tuple(date, date)): date range
                (start_date, end_date) for which the account statement was
                generated.
            input_file (str): file name including absolute path of the
                downloaded account statement for this platform.

        """
        self.platform = platform
        self.date_range = date_range
        self.df = p2p_helper.get_df_from_file(input_file)

    def _add_missing_months(self) -> None:
        """
        Add a zero row for all months in date_range without cashflows.

        To ensure that months without cashflows show up in the final output
        file this method will create one new row in the DataFrame self.df for
        each month in date_range without cashflows.

        """
        # Get a list of all months in date_range with no cashflows
        missing_months = self._get_missing_months()

        # Create list of dates set to the first of each missing month
        new_cf_dates = []
        for month in missing_months:
            new_cf_dates.append(datetime(
                month[0].year, month[0].month, month[0].day))

        # Set all entries in the columns of the new DataFrame to zero, except
        # for the DATE and CURRENCY column
        content = dict()
        zeroes = [0.] * len(new_cf_dates)
        for column in self.TARGET_COLUMNS:
            content[column] = zeroes
        content[self.DATE] = new_cf_dates
        content[self.CURRENCY] = 'EUR'

        # Create the new DataFrame and append it to the old one
        df_new = pd.DataFrame(data=content, columns=self.TARGET_COLUMNS)
        if self.df.empty:
            self.df = df_new
        else:
            self.df = self.df.append(df_new, sort=False)

        # Fill missing values with zero and sort the whole DataFrame by date
        self.df.fillna(0., inplace=True)
        self.df.sort_values(by=[self.DATE], inplace = True)

    def _get_missing_months(self) -> List[Tuple[date, date]]:
        """
        Get list of months in date_range which have no cashflows.

        This method will identify all months in date_range which do not contain
        at least one cashflow in the provided DataFrame. A list of those months
        is returned.

        Returns:
            List[Tuple[date, date]]: list of month tuples
                (start_of_month, end_of_month) which do not contain a cashflow.

        """
        # Get a list of all months in date_range
        list_of_months = p2p_helper.get_list_of_months(self.date_range)

        # If there were no cashflows all months are missing
        if self.df.empty:
            return list_of_months

        # Get all cashflow dates in date format from the DataFrame
        cf_date_list = []
        for elem in self.df[self.DATE].tolist():
            cf_date_list.append(date(elem.year, elem.month, elem.day))

        # Remove all months for which there is at least one cashflow
        for cf_date in cf_date_list:
            for month in list_of_months:
                if month[0] <= cf_date <= month[1]:
                    list_of_months.remove(month)

        return list_of_months

    def _calculate_total_income(self):
        """ Calculate total income for each row of the DataFrame"""
        income_columns = [
            self.INTEREST_PAYMENT,
            self.LATE_FEE_PAYMENT,
            self.BUYBACK_INTEREST_PAYMENT,
            self.DEFAULTS ]
        self.df[self.TOTAL_INCOME] = 0.
        for col in [col for col in self.df.columns if col in income_columns]:
            self.df[self.TOTAL_INCOME] += self.df[col]

    def _check_unknown_cf_types(self, orig_cf_column: str) -> str:
        """
        Helper method to identify any unknown cash flow types.

        Args:
            orig_cf_column (str): name of data frame column which contains
            the cash flow types as reported by the P2P platform

        Returns:
            str: string consisting of all unknown cash flow types

        """
        unknown_cf_types = set(self.df[orig_cf_column].where(
            self.df['Cashflow-Typ'].isna()).dropna().tolist())
        return ', '.join(sorted(unknown_cf_types))

    def _aggregate_df(self, value_column: Optional[str] = None) -> None:
        """
        Helper method to aggregate results by date and currency.

        Args:
            value_column (str): name of the DataFrame column which contains the
                data to be aggregated

        """
        if value_column:
            self.df = pd.pivot_table(
                self.df, values=value_column, index=[self.DATE, self.CURRENCY],
                columns=['Cashflow-Typ'], aggfunc=sum)
            self.df.reset_index(inplace=True)
        self.df.fillna(0, inplace=True)
        try:
            self.df[self.DATE] = pd.to_datetime(
                self.df[self.DATE], format='%d.%m.%Y')
        except KeyError:
            # If the DataFrame is empty this error occurs and can be ignored
            pass

    def parse_statement(
            self, date_format: Optional[str] = None,
            rename_columns: Optional[Mapping[str, str]] = None,
            cashflow_types: Optional[Mapping[str, str]] = None,
            orig_cf_column: Optional[str] = None,
            value_column: Optional[str] = None) -> None:
        """
        Parse the statement from platform format into easyP2P format.

        Keyword Args:
            date_format (str): date format which the platform uses.
            rename_columns (dict(str, str)): a dictionary containing a mapping
                between platform and easyP2P column names.
            cashflow_types (dict(str, str)): a dictionary containing a mapping
                between platform and easyP2P cashflow types.
            orig_cf_column (str): name of the column which contains the
                platform cashflow type.
            value_column (str): name of the DataFrame column which contains the
                data to be aggregated.

        """
        if rename_columns:
            self.df.rename(columns=rename_columns, inplace=True)

        if date_format:
            try:
                self.df[self.DATE] = pd.to_datetime(
                    self.df[self.DATE], format=date_format)
                self.df[self.DATE] = self.df[self.DATE].dt.strftime('%d.%m.%Y')
            except KeyError:
                raise RuntimeError(
                    '{0}: Datumsspalte nicht im Kontoauszug vorhanden!'
                    .format(self.platform))

        if cashflow_types:
            try:
                self.df['Cashflow-Typ'] = self.df[orig_cf_column].map(
                    cashflow_types)
                unknown_cf_types = self._check_unknown_cf_types(orig_cf_column)
            except KeyError:
                raise RuntimeError(
                    '{0}: Cashflowspalte nicht im Kontoauszug vorhanden!'
                    .format(self.platform))
        else:
            unknown_cf_types = ''

        # easyP2P (currently) only supports EUR
        if self.CURRENCY not in self.df.columns:
            self.df[self.CURRENCY] = 'EUR'

        self._aggregate_df(value_column)
        self._add_missing_months()
        self._calculate_total_income()
        self.df[self.PLATFORM] = self.platform
        self.df.set_index(
            [self.PLATFORM, self.DATE, self.CURRENCY], inplace=True)

        return unknown_cf_types


def bondora(
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
        'Zeitraum': parser.DATE }

    unknown_cf_types = parser.parse_statement(
        '%b %Y', rename_columns=rename_columns)

    return (parser.df, unknown_cf_types)


def mintos(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/mintos_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Mintos.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Mintos web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Mintos', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    try:
        # Create new columns for identifying cashflow types
        parser.df['Mintos_Cashflow-Typ'], parser.df['Loan ID'] = \
            parser.df['Details'].str.split(' Loan ID: ').str
        parser.df['Mintos_Cashflow-Typ'] = \
            parser.df['Mintos_Cashflow-Typ'].str.split(' Rebuy purpose').str[0]
    except KeyError as err:
        raise RuntimeError('Mintos: unbekannte Spalte im Parser: ' + str(err))

    # Define mapping between Mintos and easyP2P cashflow types and column names
    cashflow_types = {
        # Treat bonus/cashback payments as normal interest payments:
        'Cashback bonus': parser.INTEREST_PAYMENT,
        'Delayed interest income on rebuy': parser.BUYBACK_INTEREST_PAYMENT,
        'Interest income': parser.INTEREST_PAYMENT,
        'Interest income on rebuy': parser.BUYBACK_INTEREST_PAYMENT,
        'Investment principal rebuy': parser.BUYBACK_PAYMENT,
        'Investment principal increase': parser.INVESTMENT_PAYMENT,
        'Investment principal repayment': parser.REDEMPTION_PAYMENT,
        'Incoming client payment': parser.INCOMING_PAYMENT,
        'Late payment fee income': parser.LATE_FEE_PAYMENT,
        'Reversed incoming client payment': parser.OUTGOING_PAYMENT }
    rename_columns = {'Currency': parser.CURRENCY, 'Date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
        'Mintos_Cashflow-Typ', 'Turnover')

    # TODO: get start and end balance

    return (parser.df, unknown_cf_types)


def robocash(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/robocash_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Robocash.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Robocash web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Robocash', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Define mapping between Robocash and easyP2P cashflow types and
    # column names
    cashflow_types = {
        'Darlehenskauf': parser.INVESTMENT_PAYMENT,
        'Die Geldauszahlung': parser.OUTGOING_PAYMENT,
        'Geldeinzahlung': parser.INCOMING_PAYMENT,
        'Kreditrückzahlung': parser.REDEMPTION_PAYMENT,
        'Zinsenzahlung': parser.INTEREST_PAYMENT }
    rename_columns = {'Datum und Laufzeit': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
        'Operation', 'Betrag')

    return (parser.df, unknown_cf_types)


def swaper(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/swaper_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Swaper.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Swaper web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Swaper', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Define mapping between Swaper and easyP2P cashflow types and column names
    cashflow_types = {
        'BUYBACK_INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK_PRINCIPAL': parser.BUYBACK_PAYMENT,
        'EXTENSION_INTEREST': parser.INTEREST_PAYMENT,
        'INVESTMENT': parser.INVESTMENT_PAYMENT,
        'REPAYMENT_INTEREST': parser.INTEREST_PAYMENT,
        'REPAYMENT_PRINCIPAL': parser.REDEMPTION_PAYMENT }
    rename_columns = {'Booking date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d.%m.%Y', rename_columns, cashflow_types,
        'Transaction type', 'Amount')

    return (parser.df, unknown_cf_types)


def peerberry(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/peerberry_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Peerberry.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the PeerBerry web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('PeerBerry', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Define mapping between PeerBerry and easyP2P cashflow types and column
    # names
    cashflow_types = {
        'Amount of interest payment received': parser.INTEREST_PAYMENT,
        'Amount of principal payment received': parser.REDEMPTION_PAYMENT,
        'Investment': parser.INVESTMENT_PAYMENT }
    rename_columns = {'Currency Id': parser.CURRENCY, 'Date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

    return (parser.df, unknown_cf_types)


def estateguru(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/estateguru_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Estateguru.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Estateguru web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Estateguru', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Drop last line which only contains a summary
    parser.df = parser.df[:-1]

    # Define mapping between Estateguru and easyP2P cashflow types and column
    # names
    cashflow_types = {
        # Treat bonus payments as normal interest payments
        'Bonus': parser.INTEREST_PAYMENT,
        'Einzahlung(Banktransfer)': parser.INCOMING_PAYMENT,
        'Entschädigung': parser.LATE_FEE_PAYMENT,
        'Hauptbetrag': parser.REDEMPTION_PAYMENT,
        'Investition(Auto Investieren)': parser.INVESTMENT_PAYMENT,
        'Zins': parser.INTEREST_PAYMENT }
    rename_columns = {
        'Cashflow-Typ': 'Estateguru_Cashflow-Typ',
        'Zahlungsdatum': parser.DATE }

    unknown_cf_types = parser.parse_statement(
        '%d/%m/%Y %H:%M', rename_columns, cashflow_types,
        'Estateguru_Cashflow-Typ', 'Betrag')

    return (parser.df, unknown_cf_types)


def iuvo(
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
                parser.INVESTMENT_PAYMENT }

    unknown_cf_types = parser.parse_statement('%d.%m.%Y', rename_columns)

    return (parser.df, unknown_cf_types)


def grupeer(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/grupeer_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Grupeer.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Grupeer web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Grupeer', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Get the currency from the Description column and replace known currencies
    # with their ISO code
    parser.df[parser.CURRENCY], parser.df['Details'] \
        = parser.df['Description'].str.split(';').str
    rename_currency = {'&euro': 'EUR', 'Gekauft &euro': 'EUR'}
    parser.df[parser.CURRENCY].replace(rename_currency, inplace=True)

    # Convert amount to float64
    parser.df['Amount'] = parser.df['Amount'].apply(
        lambda x: x.replace(',', '.')).astype('float64')

    # Define mapping between Grupeer and easyP2P cashflow types and column names
    cashflow_types = {
        # Treat cashback as interest payment:
        'Cashback': parser.INTEREST_PAYMENT,
        'Deposit': parser.INCOMING_PAYMENT,
        'Interest': parser.INTEREST_PAYMENT,
        'Investment': parser.INVESTMENT_PAYMENT,
        'Principal': parser.REDEMPTION_PAYMENT }
    rename_columns = {'Date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d.%m.%Y', rename_columns, cashflow_types, 'Type', 'Amount')

    return (parser.df, unknown_cf_types)


def dofinance(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/dofinance_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for DoFinance.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the DoFinance web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('DoFinance', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Drop the last two rows which only contain a summary
    parser.df = parser.df[:-2]

    # Define mapping between DoFinance and easyP2P cashflow types and column
    # names
    cashflow_types = {
        'Abhebungen': parser.OUTGOING_PAYMENT,
        'Gewinn': parser.INTEREST_PAYMENT }

    for interest_rate in ['5%', '7%', '9%', '12%']:
        cashflow_types[
            'Rückzahlung\nRate: {0} Typ: automatisch'.format(interest_rate)] \
            = parser.REDEMPTION_PAYMENT
        cashflow_types[
            'Anlage\nRate: {0} Typ: automatisch'.format(interest_rate)] \
            = parser.INVESTMENT_PAYMENT

    rename_columns = {'Bearbeitungsdatum': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d.%m.%Y', rename_columns, cashflow_types, 'Art der Transaktion',
        'Betrag, €')

    return (parser.df, unknown_cf_types)


def twino(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/twino_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Twino.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Twino web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Twino', date_range, input_file)

    # Format the header of the table
    parser.df = parser.df[1:]  # The first row only contains a generic header
    new_header = parser.df.iloc[0] # Get the new first row as header
    parser.df = parser.df[1:] # Remove the first row
    parser.df.columns = new_header # Set the new header

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Create a new column for identifying cashflow types
    try:
        parser.df['Twino_Cashflow-Typ'] = parser.df['Type'] + ' ' \
            + parser.df['Description']
    except KeyError:
        raise RuntimeError(
            'Twino: Cashflowspalte nicht im Kontoauszug vorhanden!')

    # Define mapping between Twino and easyP2P cashflow types and column names
    cashflow_types = {
        'BUYBACK INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK PRINCIPAL': parser.BUYBACK_PAYMENT,
        'BUY_SHARES PRINCIPAL': parser.INVESTMENT_PAYMENT,
        'EXTENSION INTEREST': parser.INTEREST_PAYMENT,
        'REPAYMENT INTEREST': parser.INTEREST_PAYMENT,
        'REPAYMENT PRINCIPAL': parser.REDEMPTION_PAYMENT,
        'REPURCHASE INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
        'REPURCHASE PRINCIPAL': parser.BUYBACK_PAYMENT,
        'SCHEDULE INTEREST': parser.INTEREST_PAYMENT
        }
    rename_columns = {'Processing Date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d.%m.%Y %H:%M', rename_columns, cashflow_types, 'Twino_Cashflow-Typ',
        'Amount, EUR')

    return (parser.df, unknown_cf_types)


def show_results(
        list_of_dfs: Sequence[pd.DataFrame],
        date_range: Tuple[date, date],
        output_file: str) -> bool:
    """
    Sum up the results contained in data frames and write them to an Excel file.

    The results are presented in two ways: on a monthly basis (in the Excel tab
    'Monatsergebnisse') and the total sums (in tab 'Gesamtergebnis') for the
    period between start and end date.

    Args:
        df (pandas.DataFrame): data frame containing the combined data from
            the P2P platforms
        start_date (datetime.date): start of the evaluation period
        end_date (datetime.date): end of the evaluation period
        output_file (str): absolute path to the output file

    Returns:
        bool: True on success, False on failure

    """
    df = pd.DataFrame()
    for elem in list_of_dfs:
        if df.empty:
            df = elem
        else:
            df = df.append(elem, sort=True).fillna(0.)

    if df.empty:
        return False

    # Show only existing columns
    show_columns = [col for col in df.columns if col in TARGET_COLUMNS]

    df.reset_index(level=['Datum', 'Währung'], inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
    df['Monat'] = pd.to_datetime(
        df['Datum'], format='%d.%m.%Y').dt.to_period('M')
    df = df.round(2)

    # Make sure we only show results between start and end date
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])
    df = df[(df['Datum'] >= start_date) & (df['Datum'] <= end_date)]

    # Write monthly results to file
    writer = pd.ExcelWriter(output_file)
    month_pivot_table = pd.pivot_table(
        df, values=show_columns,
        index=['Plattform', 'Währung', 'Monat'], aggfunc=sum)
    month_pivot_table.to_excel(writer, 'Monatsergebnisse')

    totals_pivot_table = pd.pivot_table(
        df, values=show_columns,
        index=['Plattform', 'Währung'], aggfunc=sum)

    if 'Startguthaben' in totals_pivot_table.columns:
        for index in month_pivot_table.index.levels[0]:
            start_balance = month_pivot_table.loc[index]['Startguthaben'][0]
            totals_pivot_table.loc[index]['Startguthaben'] = start_balance
    if 'Endsaldo' in totals_pivot_table.columns:
        for index in month_pivot_table.index.levels[0]:
            end_balance = month_pivot_table.loc[index]['Endsaldo'][0]
            totals_pivot_table.loc[index]['Endsaldo'] = end_balance

    # Write total results to file
    totals_pivot_table.to_excel(writer, 'Gesamtergebnis')
    writer.save()

    return True
