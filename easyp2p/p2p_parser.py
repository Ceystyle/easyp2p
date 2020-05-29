# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module for parsing output files of P2P platforms and printing combined results.

Each P2P platform has a unique format for presenting investment results. The
purpose of this module is to provide parser methods to transform them into a
single output format.

"""
from datetime import date
import logging
from pathlib import Path
from typing import Mapping, Optional, Tuple

import numpy as np
import pandas as pd
from pandas.errors import ParserError
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate
logger = logging.getLogger('easyp2p.p2p_parser')


class P2PParser:
    """
    Parser class to transform P2P account statements into easyp2p format.

    Each P2P platform uses a unique format for their account statements. The
    purpose of P2PParser is to provide parser methods for transforming those
    files into a single unified easyp2p statement format.

    """
    # Signals for communicating with the GUI
    signals = Signals()

    # Define all necessary payment types
    INTEREST_PAYMENT = _translate('P2PParser', 'Interest payments')
    BUYBACK_INTEREST_PAYMENT = _translate(
        'P2PParser', 'Buyback interest payments')
    BUYBACK_PAYMENT = _translate('P2PParser', 'Buybacks')
    INVESTMENT_PAYMENT = _translate('P2PParser', 'Investments')
    IGNORE = 'Ignored'
    REDEMPTION_PAYMENT = _translate('P2PParser', 'Redemption payments')
    LATE_FEE_PAYMENT = _translate('P2PParser', 'Late fee payments')
    IN_OUT_PAYMENT = _translate('P2PParser', 'Deposit/Outpayment')
    DEFAULTS = _translate('P2PParser', 'Defaults')
    START_BALANCE_NAME = _translate('P2PParser', 'Start balance')
    END_BALANCE_NAME = _translate('P2PParser', 'End balance')
    TOTAL_INCOME = _translate('P2PParser', 'Total income')

    # Define additional column names
    DATE = _translate('P2PParser', 'Date')
    MONTH = _translate('P2PParser', 'Month')
    PLATFORM = _translate('P2PParser', 'Platform')
    CURRENCY = _translate('P2PParser', 'Currency')
    CF_TYPE = 'Cash flow type'

    # TARGET_COLUMNS are the columns which will be shown in the final result
    # file
    TARGET_COLUMNS = [
        START_BALANCE_NAME,
        END_BALANCE_NAME,
        IN_OUT_PAYMENT,
        INVESTMENT_PAYMENT,
        REDEMPTION_PAYMENT,
        BUYBACK_PAYMENT,
        INTEREST_PAYMENT,
        BUYBACK_INTEREST_PAYMENT,
        LATE_FEE_PAYMENT,
        DEFAULTS,
        TOTAL_INCOME]

    @signals.watch_errors
    def __init__(
            self, name: str, date_range: Tuple[date, date],
            statement_file_name: str, header: int = 0,
            skipfooter: int = 0, signals: Optional[Signals] = None) -> None:
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
            signals: Signals instance for communicating with the calling class.

        Raises:
            RuntimeError: If the account statement could not be loaded from
                statement file

        """
        self.name = name
        self.date_range = date_range
        self.statement_file_name = statement_file_name
        self.df = get_df_from_file(
            self.statement_file_name, header=header, skipfooter=skipfooter)
        self.logger = logging.getLogger('easyp2p.p2p_parser.P2PParser')
        if signals:
            self.signals.connect_signals(signals)

        # Check if account statement exists
        if self.df is None:
            raise RuntimeError(_translate(
                'P2PParser',
                f'{self.name} parser: no account statement available!'))
        self.logger.debug('Created P2PParser instance for %s.', self.name)

    def _calculate_total_income(self):
        """ Calculate total income for each row of the DataFrame """
        self.logger.debug('%s: calculating total income.', self.name)
        income_columns = [
            self.INTEREST_PAYMENT,
            self.LATE_FEE_PAYMENT,
            self.BUYBACK_INTEREST_PAYMENT,
            self.DEFAULTS]
        self.df[self.TOTAL_INCOME] = 0.
        for col in [col for col in self.df.columns if col in income_columns]:
            self.df[self.TOTAL_INCOME] += self.df[col]
        self.logger.debug('%s: finished calculating total income.', self.name)

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
        self.logger.debug(
            '%s: start aggregating results in column %s.',
            self.name, value_column)
        orig_df = self.df
        if value_column:
            self.df = self.df.pivot_table(
                values=value_column, index=[self.DATE, self.CURRENCY],
                columns=[self.CF_TYPE], aggfunc=np.sum)
            self.df.reset_index(inplace=True)
        self.df.fillna(0, inplace=True)

        # Start and end balance columns were summed up as well if they were
        # present. That's obviously not correct, so we will look up the correct
        # values in the original DataFrame and overwrite the sums.
        if balance_column:
            # The start balance value of each day already includes the first
            # daily cash flow which needs to be subtracted again
            self.df[self.START_BALANCE_NAME] = \
                (orig_df.groupby([self.DATE, self.CURRENCY]).first()[
                    balance_column]
                 - orig_df.groupby(self.DATE).first()[
                     value_column]).reset_index()[0]
            self.df[self.END_BALANCE_NAME] = \
                orig_df.groupby([self.DATE, self.CURRENCY]).last()[
                    balance_column].reset_index()[balance_column]
        self.logger.debug('%s: finished aggregating results.', self.name)

    def _filter_date_range(self, date_format: str) -> None:
        """
        Only keep dates in data range self.date_range in DataFrame self.df.

        Args:
            date_format: Date format which the platform uses

        """
        self.logger.debug('%s: filter date range.', self.name)
        start_date = pd.Timestamp(self.date_range[0])
        end_date = pd.Timestamp(self.date_range[1]).replace(
            hour=23, minute=59, second=59)
        self.df[self.DATE] = pd.to_datetime(
            self.df[self.DATE], format=date_format)
        self.df = self.df[
            (self.df[self.DATE] >= start_date)
            & (self.df[self.DATE] <= end_date)]
        # Convert date column from datetime to date:
        self.df[self.DATE] = self.df[self.DATE].dt.date
        self.logger.debug('%s: filter date range finished.', self.name)

    def _map_cashflow_types(
            self, cashflow_types: Optional[Mapping[str, str]],
            orig_cf_column: Optional[str]) -> Tuple[str, ...]:
        """
        Map platform cashflow types to easyp2p cashflow types.

        Args:
            cashflow_types: Dictionary containing a mapping between platform
                and easyp2p cash flow types
            orig_cf_column: Name of the column in the platform account
                statement which contains the cash flow type

        Returns:
            Sorted tuple of strings with all unknown cash flow types or an
            empty tuple if no unknown cash flow types were found.

        """
        if cashflow_types:
            self.logger.debug(
                '%s: mapping cash flow types %s contained in column %s.',
                self.name, str(cashflow_types.keys()), orig_cf_column)
            self.df[self.CF_TYPE] = self.df[orig_cf_column].map(cashflow_types)
            # All unknown cash flow types will be NaN
            unknown_cf_types = self.df[orig_cf_column].where(
                self.df[self.CF_TYPE].isna()).dropna().tolist()
            # Remove duplicates, sort the entries and make them immutable
            unknown_cf_types = tuple(sorted(set(unknown_cf_types)))
            self.logger.debug('%s: mapping successful.', self.name)
            return unknown_cf_types

        self.logger.debug('%s: no cash flow types to map.', self.name)
        return ()

    def _add_zero_line(self):
        """Add a single zero cash flow for start date to the DataFrame."""
        self.logger.debug('%s: adding zero cash flow.', self.name)
        data = [
            (self.name, 'EUR', self.date_range[0],
             *[0.] * len(self.TARGET_COLUMNS))]
        columns = [
            self.PLATFORM, self.CURRENCY, self.DATE,
            *self.TARGET_COLUMNS]
        self.df = pd.DataFrame(data=data, columns=columns)
        self.df.set_index(
            [self.PLATFORM, self.CURRENCY, self.DATE], inplace=True)
        self.logger.debug('%s: added zero cash flow.', self.name)

    @signals.update_progress
    def run(
            self, date_format: str = None,
            rename_columns: Mapping[str, str] = None,
            cashflow_types: Optional[Mapping[str, str]] = None,
            orig_cf_column: Optional[str] = None,
            value_column: Optional[str] = None,
            balance_column: Optional[str] = None) -> Tuple[str, ...]:
        """
        Parse the account statement from platform format to easyp2p format.

        Keyword Args:
            date_format: Date format which the platform uses
            rename_columns: Dictionary containing a mapping between platform
                and easyp2p column names
            cashflow_types: Dictionary containing a mapping between platform
                and easyp2p cash flow types
            orig_cf_column: Name of the column in the platform account
                statement which contains the cash flow type
            value_column: Name of the DataFrame column which contains the
                amounts to be aggregated
            balance_column: Name of the column which contains the portfolio
                balances

        Returns:
            Sorted tuple of all unknown cash flow types as strings.

        Raises:
            RuntimeError: If date or cash flow columns cannot be found in
                DataFrame

        """
        self.logger.debug('%s: starting parser.', self.name)
        # If there were no cash flows in date_range add a single zero line
        if self.df.empty:
            self._add_zero_line()
            return ()

        try:
            # Rename columns in DataFrame
            if rename_columns:
                self.df.rename(columns=rename_columns, inplace=True)

            # Make sure we only show results between start and end date
            if date_format:
                self._filter_date_range(date_format)
                if self.df.empty:
                    self._add_zero_line()
                    return ()

            # Convert cash flow types from platform to easyp2p types
            unknown_cf_types = self._map_cashflow_types(
                cashflow_types, orig_cf_column)
        except KeyError as err:
            self.logger.exception(
                '%s: column missing in account statement.', self.name)
            raise RuntimeError(_translate(
                'P2PParser',
                f'{self.name}: column {str(err)} is missing in account '
                'statement!'))

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
            [self.PLATFORM, self.CURRENCY, self.DATE], inplace=True)

        # Sort and drop all unnecessary columns
        self.df = self.df[[
            col for col in self.TARGET_COLUMNS if col in self.df.columns]]

        # Disconnect signals
        if self.signals:
            self.signals.disconnect_signals()

        self.logger.debug('%s: parser completed successfully.', self.name)
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
            if skipfooter:
                # The default 'c' engine does not support skipfooter
                df = pd.read_csv(
                    input_file, header=header, skipfooter=skipfooter,
                    engine='python')
            else:
                df = pd.read_csv(input_file, header=header)
        elif file_format in ('.xlsx', '.xls'):
            df = pd.read_excel(input_file, header=header, skipfooter=skipfooter)
        else:
            raise RuntimeError(_translate(
                'P2PParser', 'Unknown file format during import:'), input_file)
    except FileNotFoundError:
        logger.exception('File not found.')
        raise RuntimeError(_translate(
            'P2PParser', f'{input_file} could not be found!'))
    except ParserError:
        msg = f'{input_file} could not be parsed!'
        logger.exception(msg)
        raise RuntimeError(_translate('P2PParser', msg))

    return df
