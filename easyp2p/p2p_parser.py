# -*- coding: utf-8 -*-

"""
Module for parsing output files of P2P platforms and printing combined results.

    Each P2P platform has a unique format for presenting investment results.
    The purpose of this module is to provide parser methods to transform them
    into a single output format. The combined output is aggregated and
    written to an Excel file.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""
from datetime import date
from typing import List, Mapping, Optional, Sequence, Tuple

import pandas as pd
import p2p_helper


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
        START_BALANCE_NAME,
        END_BALANCE_NAME,
        TOTAL_INCOME,
        INTEREST_PAYMENT,
        INVESTMENT_PAYMENT,
        REDEMPTION_PAYMENT,
        BUYBACK_PAYMENT,
        BUYBACK_INTEREST_PAYMENT,
        LATE_FEE_PAYMENT,
        DEFAULTS]

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
            new_cf_dates.append(
                date(month[0].year, month[0].month, month[0].day))

        # Create the new DataFrame and append it to the old one
        df_new = pd.DataFrame(
            data={self.DATE: new_cf_dates, self.CURRENCY: 'EUR'},
            columns=[self.DATE, self.CURRENCY])

        if self.df.empty:
            self.df = df_new
        else:
            self.df = self.df.append(df_new, sort=True)

        # Fill missing values with zero and sort the whole DataFrame by date
        self.df.fillna(0., inplace=True)
        self.df.sort_values(by=[self.DATE], inplace=True)

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
        for elem in pd.to_datetime(self.df[self.DATE]).tolist():
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
            self.DEFAULTS]
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

    def parse_statement(
            self, date_format: Optional[str] = None,
            rename_columns: Optional[Mapping[str, str]] = None,
            cashflow_types: Optional[Mapping[str, str]] = None,
            orig_cf_column: Optional[str] = None,
            value_column: Optional[str] = None) -> str:
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

        # Make sure we only show results between start and end date
        start_date = pd.Timestamp(self.date_range[0])
        end_date = pd.Timestamp(self.date_range[1])

        if date_format:
            try:
                self.df[self.DATE] = pd.to_datetime(
                    self.df[self.DATE], format=date_format)
                self.df = self.df[(self.df[self.DATE] >= start_date) \
                    & (self.df[self.DATE] <= end_date)]
                self.df[self.DATE] = self.df[self.DATE].dt.date
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

        # Add missing columns
        for col in [
                col for col in self.TARGET_COLUMNS
                if col not in self.df.columns]:
            self.df[col] = 'NaN'

        self.df.set_index(
            [self.PLATFORM, self.DATE, self.CURRENCY], inplace=True)

        return unknown_cf_types


def show_results(
        list_of_dfs: Sequence[pd.DataFrame], output_file: str) -> bool:
    """
    Sum up the results contained in data frames and write them to Excel file.

    The results are presented in two ways: on a monthly basis (in the Excel tab
    'Monatsergebnisse') and the total sums (in tab 'Gesamtergebnis') for the
    period between start and end date.

    Args:
        df (pandas.DataFrame): data frame containing the combined data from
            the P2P platforms
        output_file (str): absolute path to the output file

    Returns:
        bool: True on success, False on failure

    """
    df_monthly = pd.DataFrame()
    df_total = pd.DataFrame()

    for df in list_of_dfs:
        df.reset_index(inplace=True)
        df[P2PParser.DATE] = pd.to_datetime(
            df[P2PParser.DATE], format='%Y-%m-%d')
        df[P2PParser.MONTH] = pd.to_datetime(
            df[P2PParser.DATE], format='%d.%m.%Y').dt.to_period('M')

        # We need to fill the NaNs with a dummy value so they don't disappear
        # when creating the pivot tables
        df.fillna('dummy', inplace=True)

        df_pivot = pd.pivot_table(
            df, values=P2PParser.TARGET_COLUMNS,
            index=[P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.MONTH],
            aggfunc=sum, dropna=False)
        df_monthly = df_monthly.append(df_pivot, sort=True)
        df_pivot = pd.pivot_table(
            df, values=P2PParser.TARGET_COLUMNS,
            index=[P2PParser.PLATFORM, P2PParser.CURRENCY], aggfunc=sum)
        df_total = df_total.append(df_pivot, sort=True)

    if df_total.empty:
        return False

    # Round all results to 2 digits
    df_monthly = df_monthly.round(2)
    df_total = df_total.round(2)

    # Write monthly results to file
    writer = pd.ExcelWriter(output_file, date_format='%d.%m.%Y')
    df_monthly.to_excel(writer, 'Monatsergebnisse')

    # Start and end balance columns were summed up as well if they are present.
    # That's obviously not correct, so we will look up the correct values
    # in the monthly table and overwrite the sums.
    if P2PParser.START_BALANCE_NAME in df_total.columns:
        for index in df_total.index.levels[0]:
            start_balance = df_monthly.loc[index][P2PParser.START_BALANCE_NAME][0]
            df_total.loc[index][P2PParser.START_BALANCE_NAME] = start_balance
    if P2PParser.END_BALANCE_NAME in df_total.columns:
        for index in df_total.index.levels[0]:
            end_balance = df_monthly.loc[index][P2PParser.END_BALANCE_NAME][-1]
            df_total.loc[index][P2PParser.END_BALANCE_NAME] = end_balance

    # Write total results to file
    df_total.to_excel(writer, 'Gesamtergebnis')
    writer.save()

    return True