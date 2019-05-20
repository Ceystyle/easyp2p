# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Module for parsing output files of P2P platforms and printing combined results.

Each P2P platform has a unique format for presenting investment results. The
purpose of this module is to provide parser methods to transform them into a
single output format. The combined output is aggregated and written to an Excel
file.

"""
import calendar
from datetime import date, timedelta
from pathlib import Path
from typing import List, Mapping, Optional, Sequence, Tuple

import pandas as pd

DAILY_RESULTS = 'Tagesergebnisse'
MONTHLY_RESULTS = 'Monatsergebnisse'
TOTAL_RESULTS = 'Gesamtergebnis'


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

        Raises:
            RuntimeError: If the account statement could not be loaded from
                statement file

        """
        self.name = name
        self.date_range = date_range
        self.statement_file_name = statement_file_name
        self.df = get_df_from_file(self.statement_file_name)

        # Check if account statement exists
        if self.df is None:
            raise RuntimeError(
                '{0}-Parser: kein Kontoauszug vorhanden!'.format(self.name))

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
        list_of_months = _get_list_of_months(self.date_range)

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
                (orig_df.groupby(self.DATE).first()[balance_column]
                 - orig_df.groupby(self.DATE).first()[
                     value_column]).reset_index()[0]
            self.df[self.END_BALANCE_NAME] = \
                orig_df.groupby(self.DATE).last()[
                    balance_column].reset_index()[balance_column]

    def _filter_date_range(self, date_format: str) -> None:
        """
        Only keep dates in data range self.date_range in DataFrame self.df.

        Args:
            date_format: Date format which the platform uses

        Raises:
            RuntimeError: If date column cannot be found in dataframe.

        """
        start_date = pd.Timestamp(self.date_range[0])
        end_date = pd.Timestamp(self.date_range[1]).replace(
            hour=23, minute=59, second=59)
        try:
            self.df[self.DATE] = pd.to_datetime(
                self.df[self.DATE], format=date_format)
            self.df = self.df[
                (self.df[self.DATE] >= start_date)
                & (self.df[self.DATE] <= end_date)]
            # Convert date column from datetime to date:
            self.df[self.DATE] = self.df[self.DATE].dt.date
        except KeyError as err:
            if self.df.empty:
                pass
            else:
                raise RuntimeError(
                    '{0}: Spalte {1} nicht im Kontoauszug vorhanden!'.format(
                        self.name, str(err)))

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
            Sorted string with all unknown cash flow types, separated by
            commas.

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
                    '{0}: Cashflowspalte {1} nicht im Kontoauszug '
                    'vorhanden!'.format(self.name, orig_cf_column))
        else:
            return ''

    def add_zero_cashflows(self, date_list: Sequence[date] = None):
        """
        Add a zero cashflow row to self.df for each date in date_list.

        If no date_list is provided, one zero row will be added for each month
        in self.date_range.

        Keyword Args:
            date_list: List of dates for which to add zero entries.

        """
        if not date_list:
            list_of_months = _get_list_of_months(self.date_range)
            date_list = [month[0] for month in list_of_months]

        df = pd.DataFrame()
        df[self.DATE] = date_list
        df[self.PLATFORM] = self.name
        df[self.CURRENCY] = 'EUR'
        for column in self.TARGET_COLUMNS:
            df[column] = 0.
        df.set_index([self.PLATFORM, self.DATE, self.CURRENCY], inplace=True)

        if self.df.empty:
            self.df = df
        else:
            self.df = self.df.append(df, sort=True)
        self.df.dropna(axis=1, inplace=True)

    def start_parser(
            self, date_format: str = None,
            rename_columns: Mapping[str, str] = None,
            cashflow_types: Optional[Mapping[str, str]] = None,
            orig_cf_column: Optional[str] = None,
            value_column: Optional[str] = None,
            balance_column: Optional[str] = None) -> str:
        """
        Parse the account statement from platform format to easyp2p format.

        Keyword Args:
            date_format: Date format which the platform uses
            rename_columns: Dictionary containing a mapping between platform
                and easyp2p column names
            cashflow_types: Dictionary containing a mapping between platform
                and easyp2p cashflow types
            orig_cf_column: Name of the column in the platform account
                statement which contains the cash flow type
            value_column: Name of the DataFrame column which contains the
                amounts to be aggregated
            balance_column: Name of the column which contains the portfolio
                balances

        Returns:
            Sorted set of strings with all unknown cash flow types.

        Raises:
            RuntimeError: If date or cashflow columns cannot be found in
                DataFrame

        """
        # Rename columns in DataFrame
        if rename_columns:
            try:
                self.df.rename(columns=rename_columns, inplace=True)
            except KeyError as err:
                if self.df.empty:
                    pass
                else:
                    raise RuntimeError(
                        '{0}: Spalte {1} ist nicht im Kontoauszug '
                        'vorhanden!'.format(self.name, str(err)))

        # Make sure we only show results between start and end date
        if date_format:
            self._filter_date_range(date_format)

        # Check if there were cashflows in date_range, if not add a zero row
        # for each month in date_range
        if self.df.empty:
            self.add_zero_cashflows()
            return ''

        # Convert cashflow types from platform to easyp2p types
        unknown_cf_types = self._map_cashflow_types(
            cashflow_types, orig_cf_column)

        # If the platform does not explicitly report currencies assume that
        # currency is EUR
        if self.CURRENCY not in self.df.columns:
            self.df[self.CURRENCY] = 'EUR'

        # Ensure that investments have a negative sign
        try:
            investment_col = self.df.loc[
                self.df[self.CF_TYPE] == self.INVESTMENT_PAYMENT, value_column]
            if investment_col.min() > 0.:
                investment_col *= -1
            self.df.loc[
                self.df[self.CF_TYPE] == self.INVESTMENT_PAYMENT, value_column]\
                = investment_col
        except KeyError:
            pass

        # Sum up the results per date and currency
        self._aggregate_results(value_column, balance_column)

        self._calculate_total_income()
        self.df[self.PLATFORM] = self.name
        self.df.set_index(
            [self.PLATFORM, self.DATE, self.CURRENCY], inplace=True)

        # Drop all unnecessary columns
        for column in self.df.columns:
            if column not in self.TARGET_COLUMNS:
                self.df.drop(columns=column, inplace=True)

        return unknown_cf_types


def _get_list_of_months(date_range: Tuple[date, date]) \
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


def write_results(df_result: pd.DataFrame, output_file: str) -> bool:

    """
    Function for writing daily, monthly and total investment results to Excel.

    Args:
        df_result: DataFrame containing parsed account statements for all
            selected P2P platforms.
        output_file: File name including path where to save the Excel file.

    Returns:
        True on success, False on failure.

    Raises:
        RuntimeError: If date, platform or currency column are missing
            in df_result.

    """

    def get_daily_results() -> pd.DataFrame:
        """
        Get daily results from DataFrame.

        Returns:
            DataFrame with the daily results.

        """
        df = df_result.copy()
        df.drop(columns=P2PParser.MONTH, inplace=True)
        df.set_index(
            [P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.DATE],
            inplace=True)
        return df

    def get_monthly_results() -> pd.DataFrame:
        """
        Get monthly results from DataFrame.

        Returns:
            DataFrame with the monthly results.

        """
        # Define index for pivot table
        index = [P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.MONTH]
        df = df_result.pivot_table(
            values=pivot_columns, index=index, aggfunc=aggfunc)
        df = add_balances(df, df_result, index)
        return df

    def get_total_results() -> pd.DataFrame:
        """
        Get total results from DataFrame.

        Returns:
            DataFrame with the total results.

        """
        # Define index for pivot table
        index = [P2PParser.PLATFORM, P2PParser.CURRENCY]

        df = df_monthly.pivot_table(
            values=pivot_columns, index=index, aggfunc=aggfunc, margins=True,
            dropna=False, margins_name='Total')
        df = add_balances(df, df_monthly, index)
        return df

    def add_balances(
            df: pd.DataFrame, df_balances: pd.DataFrame,
            groupby_columns: Sequence[str]) -> pd.DataFrame:
        """
        Add balance columns to DataFrame.

        The balance columns must be treated separately since they cannot simply
        be summed up during pivot table creation like the other columns.

        Args:
            df: DataFrame to which balance columns should be added.
            df_balances: DataFrame which was used to create the pivot table.
            groupby_columns: List of column names used to create the pivot
                table.

        """
        try:
            df[P2PParser.START_BALANCE_NAME] = \
                df_balances.groupby(groupby_columns).first()[
                    P2PParser.START_BALANCE_NAME]
            df[P2PParser.END_BALANCE_NAME] = \
                df_balances.groupby(groupby_columns).last()[
                    P2PParser.END_BALANCE_NAME]
        except KeyError:
            pass

        return df

    def write_worksheet(worksheet_name: str, df: pd.DataFrame) -> None:
        """
        Write DataFrame to Excel worksheet and format columns.

        For each column in the worksheet the width is set to the maximum length
        * 1,2 of all entries in the column. For all non-index columns the_format
        is set to money_format.

        Args:
            worksheet_name: Name of the worksheet where DataFrame should be
                saved.
            df: DataFrame containing the data to be written to the worksheet.

        """
        # Rounds results to 2 digits, sort columns and fill in missing values
        df = df.round(2)
        df = df[[
            column for column in P2PParser.TARGET_COLUMNS
                if column in df.columns]]
        df.fillna('N/A', inplace=True)

        df.to_excel(writer, worksheet_name)
        worksheet = writer.sheets[worksheet_name]
        index_length = len(df.index.names)
        df = df.reset_index()
        for index, col in enumerate(df.columns):
            # Get length of header and longest data entry
            header_length = len(col)
            data_length = df[col].map(lambda x: len(str(x))).max()
            if index < index_length:
                worksheet.set_column(
                    index, index, max(header_length, data_length) * 1.2)
            else:
                worksheet.set_column(
                    index, index, max(header_length, data_length) * 1.2,
                    money_format)

    # Make a copy to prevent changing the original DataFrame
    df_result = df_result.copy()

    if df_result.empty:
        return False

    # Get all columns with values
    df_result.reset_index(inplace=True)
    balance_columns = [
        P2PParser.START_BALANCE_NAME, P2PParser.END_BALANCE_NAME]
    pivot_columns = [
        column for column in P2PParser.TARGET_COLUMNS
        if column in df_result.columns and column not in balance_columns]
    if not pivot_columns:
        return False

    # Make sure that all index columns are present
    for column in [P2PParser.PLATFORM, P2PParser.CURRENCY, P2PParser.DATE]:
        if column not in df_result.columns:
            raise RuntimeError(
                'Schreiben nach Excel fehlgeschlagen! Spalte {} ist nicht '
                'vorhanden!'.format(column))

    # Format date column and add month column to DataFrame
    df_result[P2PParser.DATE] = pd.to_datetime(
        df_result[P2PParser.DATE], format='%Y-%m-%d')
    df_result[P2PParser.MONTH] = pd.to_datetime(
        df_result[P2PParser.DATE], format='%d.%m.%Y').dt.to_period('M')

    # Define aggregation functions to create the pivot tables
    # Only sum up columns with at least one non-NaN value. Otherwise NaN
    # columns will be replaced by zeros when building the pivot table.
    aggfunc = lambda x: x.sum(min_count=1)

    # Get daily, monthly and total results
    df_daily = get_daily_results()
    df_monthly = get_monthly_results()
    df_total = get_total_results()

    # Write all three DataFrames to Excel
    with pd.ExcelWriter(
            output_file, datetime_format='DD.MM.YYYY',
            engine='xlsxwriter') as writer:
        # Define format for currency columns
        workbook = writer.book
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        # Write DataFrames to Excel file
        write_worksheet(DAILY_RESULTS, df_daily)
        write_worksheet(MONTHLY_RESULTS, df_monthly)
        write_worksheet(TOTAL_RESULTS, df_total)

    return True


def get_df_from_file(input_file: str, header: int = 0) -> pd.DataFrame:
    """
    Read a pandas.DataFrame from input_file.

    Args:
        input_file: File name including path.
        header: Row number to use as column names and start of data.

    Returns:
        pandas.DataFrame: DataFrame which was read from the file.

    Raises:
        RuntimeError: If input_file does not exist, cannot be read or if the \
            file format is neither csv or xlsx.

    """

    file_format = Path(input_file).suffix

    try:
        if file_format == '.csv':
            df = pd.read_csv(input_file, header=header)
        elif file_format in ('.xlsx', '.xls'):
            df = pd.read_excel(input_file, header=header)
        else:
            raise RuntimeError(
                'Unbekanntes Dateiformat beim Import: ', input_file)
    except FileNotFoundError:
        raise RuntimeError(
            '{0} konnte nicht gefunden werden!'.format(input_file))

    return df