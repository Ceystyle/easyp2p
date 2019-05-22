# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Module for parsing output files of P2P platforms and printing combined results.

Each P2P platform has a unique format for presenting investment results. The
purpose of this module is to provide parser methods to transform them into a
single output format.

"""
from datetime import date
from pathlib import Path
from typing import Mapping, Optional, Tuple

import pandas as pd


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
            statement_file_name: str, header: int = 0,
            skipfooter: int = 0) -> None:
        """
        Constructor of P2PParser class.

        Args:
            name: Name of the P2P platform
            date_range: Date range (start_date, end_date) for which the account
                statement was generated
            statement_file_name: File name including absolute path of the
                downloaded account statement for this platform
            header: Row number to use as column names and start of data in the
                statement.
            skipfooter: Rows to skip at the end of the statement.

        Raises:
            RuntimeError: If the account statement could not be loaded from
                statement file

        """
        self.name = name
        self.date_range = date_range
        self.statement_file_name = statement_file_name
        self.df = get_df_from_file(
            self.statement_file_name, header=header, skipfooter=skipfooter)

        # Check if account statement exists
        if self.df is None:
            raise RuntimeError(
                '{0}-Parser: kein Kontoauszug vorhanden!'.format(self.name))

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
            # daily cash flow which needs to be subtracted again
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

        # If there were no cash flows in date_range add a single zero line
        if self.df.empty:
            data = [
                (self.name, 'EUR', self.date_range[0],
                 *[0.]*len(self.TARGET_COLUMNS))]
            columns = [self.PLATFORM, self.CURRENCY, self.DATE,
                       *self.TARGET_COLUMNS]
            self.df = pd.DataFrame(data=data, columns=columns)
            self.df.set_index(
                [self.PLATFORM, self.CURRENCY, self.DATE], inplace=True)
            return ''

        # Convert cash flow types from platform to easyp2p types
        unknown_cf_types = self._map_cashflow_types(
            cashflow_types, orig_cf_column)

        # If the platform does not explicitly report currencies assume that
        # currency is EUR
        if self.CURRENCY not in self.df.columns:
            self.df[self.CURRENCY] = 'EUR'

        # Ensure that investment cash flows have a negative sign
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


def get_df_from_file(
        input_file: str, header: int = 0, skipfooter: int = 0) -> pd.DataFrame:
    """
    Read a pandas.DataFrame from input_file.

    Args:
        input_file: File name including path.
        header: Row number to use as column names and start of data.
        skipfooter: Rows to skip at the end of the statement.

    Returns:
        pandas.DataFrame: DataFrame which was read from the file.

    Raises:
        RuntimeError: If input_file does not exist, cannot be read or if the \
            file format is neither csv or xlsx.

    """

    file_format = Path(input_file).suffix

    try:
        if file_format == '.csv':
            df = pd.read_csv(input_file, header=header, skipfooter=skipfooter)
        elif file_format in ('.xlsx', '.xls'):
            df = pd.read_excel(input_file, header=header, skipfooter=skipfooter)
        else:
            raise RuntimeError(
                'Unbekanntes Dateiformat beim Import: ', input_file)
    except FileNotFoundError:
        raise RuntimeError(
            '{0} konnte nicht gefunden werden!'.format(input_file))

    return df
