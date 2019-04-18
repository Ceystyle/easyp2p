# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Module for parsing output files of P2P platforms and printing combined results.

Each P2P platform has a unique format for presenting investment results. The
purpose of this module is to provide parser methods to transform them into a
single output format. The combined output is aggregated and written to an Excel
file.

"""
from datetime import date
from typing import List, Mapping, Optional, Tuple

import pandas as pd
import xlsxwriter
import easyp2p.p2p_helper as p2p_helper


class P2PParser:

    """
    Parser class to transform P2P account statements into easyp2p format.

    Each P2P platform uses a unique format for their account statements. The
    purpose of P2PParser is to provide parser methods for transforming those
    files into a single unified easyp2p statement format.

    """

    # Define all necessary payment types
    INTEREST_PAYMENT = 'Zinszahlungen'
    BUYBACK_INTEREST_PAYMENT = 'Zinszahlungen aus Rückkäufen'
    BUYBACK_PAYMENT = 'Rückkäufe'
    INVESTMENT_PAYMENT = 'Investitionen'
    IGNORE = 'Ignoriert'
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
    CF_TYPE = 'Cashflow-Typ'

    # TARGET_COLUMNS are the columns which will be shown in the final result
    # file
    TARGET_COLUMNS = [
        START_BALANCE_NAME,
        END_BALANCE_NAME,
        INVESTMENT_PAYMENT,
        REDEMPTION_PAYMENT,
        BUYBACK_PAYMENT,
        INTEREST_PAYMENT,
        BUYBACK_INTEREST_PAYMENT,
        LATE_FEE_PAYMENT,
        DEFAULTS,
        TOTAL_INCOME]

    def __init__(
            self, name: str, date_range: Tuple[date, date],
            statement_file_name: str) -> None:
        """
        Constructor of P2PParser class.

        Args:
            name: Name of the P2P platform
            date_range: Date range (start_date, end_date) for which the account
                statement was generated
            statement_file_name: File name including absolute path of the
                downloaded account statement for this platform

        """
        self.name = name
        self.date_range = date_range
        self.statement_file_name = statement_file_name
        self.df = p2p_helper.get_df_from_file(self.statement_file_name)

    def _add_missing_months(self) -> None:
        """
        Add a zero row for all months in date_range without cashflows.

        To ensure that months without cash flows show up in the final output
        file this method will create one new row in the DataFrame self.df for
        each month in date_range without cash flows.

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
        at least one cash flow in the provided DataFrame. A list of those
        months is returned.

        Returns:
            List of month tuples (start_of_month, end_of_month) which do not
            contain a cash flow

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
        """ Calculate total income for each row of the DataFrame """
        income_columns = [
            self.INTEREST_PAYMENT,
            self.LATE_FEE_PAYMENT,
            self.BUYBACK_INTEREST_PAYMENT,
            self.DEFAULTS]
        self.df[self.TOTAL_INCOME] = 0.
        for col in [col for col in self.df.columns if col in income_columns]:
            self.df[self.TOTAL_INCOME] += self.df[col]

    def _aggregate_results(
            self, value_column: Optional[str],
            balance_column: Optional[str]) -> None:
        """
        Aggregate results in value_column by date and currency.

        Args:
            value_column: Name of the DataFrame column which contains the
                data to be aggregated
            balance_column: DataFrame column which contains the balances

        """
        orig_df = self.df
        if value_column:
            self.df = pd.pivot_table(
                self.df, values=value_column, index=[self.DATE, self.CURRENCY],
                columns=[self.CF_TYPE], aggfunc=sum)
            self.df.reset_index(inplace=True)
        self.df.fillna(0, inplace=True)

        # Start and end balance columns were summed up as well if they were
        # present. That's obviously not correct, so we will look up the correct
        # values in the original DataFrame and overwrite the sums.
        if balance_column:
            # The start balance value of each day already includes the first
            # daily cashflow which needs to be subtracted again
            self.df[self.START_BALANCE_NAME] = \
                (orig_df.groupby(self.DATE).first()[balance_column] \
                - orig_df.groupby(self.DATE).first()[value_column])\
                .reset_index()[0]
            self.df[self.END_BALANCE_NAME] = \
                orig_df.groupby(self.DATE).last()[balance_column]\
                .reset_index()[balance_column]

    def _filter_date_range(self, date_format: str) -> None:
        """
        Only keep dates in data range self.date_range in DataFrame self.df.

        Args:
            date_format: Date format which the platform uses

        """
        start_date = pd.Timestamp(self.date_range[0])
        end_date = pd.Timestamp(self.date_range[1]).replace(
            hour=23, minute=59, second=59)
        try:
            self.df[self.DATE] = pd.to_datetime(
                self.df[self.DATE], format=date_format)
            self.df = self.df[(self.df[self.DATE] >= start_date) \
                & (self.df[self.DATE] <= end_date)]
            # Convert date column from datetime to date:
            self.df[self.DATE] = self.df[self.DATE].dt.date
        except KeyError:
            raise RuntimeError(
                '{0}: Datumsspalte nicht im Kontoauszug vorhanden!'
                .format(self.name))

    def _map_cashflow_types(
            self, cashflow_types: Optional[Mapping[str, str]],
            orig_cf_column: Optional[str]) -> str:
        """
        Map platform cashflow types to easyp2p cashflow types.

        Args:
            cashflow_types: Dictionary containing a mapping between platform
                and easyp2p cashflow types
            orig_cf_column: Name of the column in the platform account
                statement which contains the cash flow type

        Returns:
            Sorted comma separated string consisting of all unknown cash flow
            types

        """
        if cashflow_types:
            try:
                self.df[self.CF_TYPE] = self.df[orig_cf_column].map(
                    cashflow_types)
                unknown_cf_types = set(self.df[orig_cf_column].where(
                    self.df[self.CF_TYPE].isna()).dropna().tolist())
                return ', '.join(sorted(unknown_cf_types))
            except KeyError:
                raise RuntimeError(
                    '{0}: Cashflowspalte {1} nicht im Kontoauszug vorhanden!'
                    .format(self.name, orig_cf_column))
        else:
            return ''

    def start_parser(
            self, date_format: str, rename_columns: Mapping[str, str],
            cashflow_types: Optional[Mapping[str, str]] = None,
            orig_cf_column: Optional[str] = None,
            value_column: Optional[str] = None,
            balance_column: Optional[str] = None) -> str:
        """
        Parse the account statement from platform format to easyp2p format.

        Args:
            date_format: Date format which the platform uses
            rename_columns: Dictionary containing a mapping between platform
                and easyp2p column names

        Keyword Args:
            cashflow_types: Dictionary containing a mapping between platform
                and easyp2p cashflow types
            orig_cf_column: Name of the column in the platform account
                statement which contains the cash flow type
            value_column: Name of the DataFrame column which contains the
                amounts to be aggregated
            balance_column: Name of the column which contains the portfolio
                balances

        Returns:
            Sorted comma separated string consisting of all unknown cash flow
            types

        Raises:
            RuntimeError: - If get_statement_from_file was not called first
                          - If date or cashflow columns cannot be found in
                            DataFrame

        """
        # Check if account statement exists
        if self.df is None:
            raise RuntimeError('{0}-Parser: kein Kontoauszug vorhanden!')

        # Rename columns in DataFrame
        self.df.rename(columns=rename_columns, inplace=True)

        # Make sure we only show results between start and end date
        self._filter_date_range(date_format)

        # Convert cashflow types from platform to easyp2p types
        unknown_cf_types = self._map_cashflow_types(
            cashflow_types, orig_cf_column)

        # If the platform does not explicitly report currencies assume that
        # currency is EUR
        if self.CURRENCY not in self.df.columns:
            self.df[self.CURRENCY] = 'EUR'

        # Sum up the results per month and currency
        self._aggregate_results(value_column, balance_column)

        self._add_missing_months()
        self._calculate_total_income()
        self.df[self.PLATFORM] = self.name

        self.df.set_index(
            [self.PLATFORM, self.DATE, self.CURRENCY], inplace=True)

        return unknown_cf_types


def show_results(df_result: pd.DataFrame, output_file: str) -> bool:
    """
    Sum up the results contained in data frames and write them to Excel file.

    The results are presented in two ways: on a monthly basis (in the Excel tab
    'Monatsergebnisse') and the total sums (in tab 'Gesamtergebnis') for the
    period between start and end date.

    Args:
        df_result: DataFrame containing the parsed results from all selected
            P2P platforms
        output_file: Absolute path of the output file

    Returns:
        True on success, False on failure

    """
    # Create Month column
    df_result.reset_index(inplace=True)
    df_result[P2PParser.DATE] = pd.to_datetime(
        df_result[P2PParser.DATE], format='%Y-%m-%d')
    df_result[P2PParser.MONTH] = pd.to_datetime(
        df_result[P2PParser.DATE], format='%d.%m.%Y').dt.to_period('M')

    # Calculate results per month and platform, keeping the NaNs
    value_columns = [column for column in P2PParser.TARGET_COLUMNS \
        if column in df_result.columns]
    df_monthly = pd.pivot_table(
        df_result, values=value_columns,
        index=[P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.MONTH],
        aggfunc=lambda x: x.sum(min_count=1))

    # If start and end balance columns were present they were also summed
    # up which is obviously not correct. Fill in the correct values from the
    # original df_result DataFrame.
    try:
        df_monthly[P2PParser.START_BALANCE_NAME] = df_result.groupby(
            [P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.MONTH]).first()[
                P2PParser.START_BALANCE_NAME]
        df_monthly[P2PParser.END_BALANCE_NAME] = df_result.groupby(
            [P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.MONTH]).last()[
                P2PParser.END_BALANCE_NAME]
    except KeyError:
        pass

    # Calculate results per platform
    df_total = pd.pivot_table(
        df_monthly, values=value_columns,
        index=[P2PParser.PLATFORM, P2PParser.CURRENCY],
        aggfunc=lambda x: x.sum(min_count=1), margins=True,
        margins_name='Total')

    if df_total.empty:
        return False

    # Start and end balance columns were summed up as well if they are present.
    # That's obviously not correct, so we will look up the correct values
    # in the monthly table and overwrite the sums.
    try:
        df_total[P2PParser.START_BALANCE_NAME] = df_monthly.groupby(
            [P2PParser.PLATFORM, P2PParser.CURRENCY]).first()[
                P2PParser.START_BALANCE_NAME]
        df_total[P2PParser.END_BALANCE_NAME] = df_monthly.groupby(
            [P2PParser.PLATFORM, P2PParser.CURRENCY]).last()[
                P2PParser.END_BALANCE_NAME]
    except KeyError:
        pass

    # Round all results to 2 digits
    df_monthly = df_monthly.round(2)
    df_total = df_total.round(2)

    # Sort columns
    df_monthly = df_monthly[value_columns]
    df_total = df_total[value_columns]

    # Fill empty cells with N/A
    df_monthly.fillna('N/A', inplace=True)
    df_total.fillna('N/A', inplace=True)

    # Write monthly results to file
    writer = pd.ExcelWriter(
        output_file, date_format='%d.%m.%Y', engine='xlsxwriter')
    df_monthly.to_excel(writer, 'Monatsergebnisse')

    # Write total results to file
    df_total.to_excel(writer, 'Gesamtergebnis')

    # Format columns in the Excel sheets
    workbook = writer.book
    money_format = workbook.add_format({'num_format': '0.00'})
    monthly_ws = writer.sheets['Monatsergebnisse']
    total_ws = writer.sheets['Gesamtergebnis']

    monthly_ws.set_column('D:M', None, money_format)
    _set_excel_column_width(monthly_ws, df_monthly)

    total_ws.set_column('C:L', None, money_format)
    _set_excel_column_width(total_ws, df_total)

    writer.save()

    return True

def _set_excel_column_width(
        worksheet: xlsxwriter.worksheet, df: pd.DataFrame) -> None:
    """
    Helper function to set Excel column width to header length + 1.

    Args:
        worksheet: Worksheet containing the columns to be formatted
        df: DataFrame which was used for creating the worksheet

    """
    length_list = [len(x) + 1 for x in df.columns]
    column_offset = len(df.index.names)
    for i, width in enumerate(length_list):
        worksheet.set_column(i + column_offset, i + column_offset, width)
