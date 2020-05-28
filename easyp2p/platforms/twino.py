# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Twino statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.p2p_signals import Signals, PlatformFailedError

_translate = QCoreApplication.translate


class Twino:

    """
    Contains methods for downloading/parsing Twino account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Twino class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Twino'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self) -> None:
        """
        Generate and download the Twino account statement for given date range.

        Raises:
            PlatformFailedError: If two factor authorization is enabled.

        """
        # FIXME: do not ask user twice for credentials if they are not in the
        # keyring
        username = get_credentials(self.name, self.signals)[0]
        check2fa_url = (
            f'https://www.twino.eu/ws/public/check2fa?email={username}')
        login_url = 'https://www.twino.eu/ws/public/login2fa'
        logout_url = 'https://www.twino.eu/logout'
        gen_statement_url = (
            'https://www.twino.eu/ws/web/investor/account-entries/'
            'init-export-to-excel')
        download_url = (
            f'https://www.twino.eu/ws/web/export-to-excel/{username}/'
            f'download')

        with P2PSession(self.name, logout_url, self.signals, json=True) as sess:
            resp = sess.request(
                check2fa_url, 'get', _translate(
                    'P2PPlatform', f'{self.name}: loading login page failed!'))

            if resp.json():
                raise PlatformFailedError(_translate(
                    'P2PPlatform',
                    f'{self.name}: two factor authorization is not yet '
                    f'supported in easyp2p!'))

            sess.log_into_page(login_url, 'name', 'password')

            start_date = [
                self.date_range[0].year, self.date_range[0].month,
                self.date_range[0].day]
            end_date = [
                self.date_range[1].year, self.date_range[1].month,
                self.date_range[1].day]
            data = {
                'accountTypeList': [],
                'page': 1,
                'pageSize': 20,
                'processingDateFrom': start_date,
                'processingDateTo': end_date,
                'sortDirection': 'DESC',
                'sortField': 'created',
                'totalItems': 0,
                'transactionTypeList': [
                    {'transactionType': 'REPAYMENT'},
                    {'transactionType': 'EARLY_FULL_REPAYMENT'},
                    {'transactionType': 'EARLY_PARTIAL_REPAYMENT'},
                    {'positive': False, 'transactionType': 'BUY_SHARES'},
                    {'positive': True, 'transactionType': 'BUY_SHARES'},
                    {'positive': True, 'transactionType': 'FUNDING'},
                    {'positive': False, 'transactionType': 'FUNDING'},
                    {'transactionType': 'EXTENSION'},
                    {'transactionType': 'ACCRUED_INTEREST'},
                    {'transactionType': 'BUYBACK'},
                    {'transactionType': 'SCHEDULE'},
                    {'transactionType': 'RECOVERY'},
                    {'transactionType': 'REPURCHASE'},
                    {'transactionType': 'LOSS_ON_WRITEOFF'},
                    {'transactionType': 'WRITEOFF'},
                    {'transactionType': 'CURRENCY_FLUCTUATION'},
                    {'transactionType': 'CASHBACK'},
                    {'transactionType': 'REFERRAL'},
                    {'transactionType': 'CORRECTION'},
                    {'transactionType': 'BUY_OUT'}]
            }
            sess.generate_account_statement(gen_statement_url, 'post', data)

            def download_ready():
                resp = sess.request(
                    download_url, 'get', _translate(
                        'P2PPlatform',
                        f'{self.name}: download of account statement failed!'),
                    success_codes=(200, 500))
                if resp.status_code == 200:
                    with open(self.statement, 'wb') as file:
                        file.write(resp.content)
                    return True

                if resp.status_code == 500:
                    return False

                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: download of account statement failed!'))

            sess.wait(download_ready)

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Twino.

        Args:
            statement: File name including path of the account
                statement which should be parsed. If None, the file at
                self.statement will be parsed. Default is None.

        Returns:
            Tuple with two elements. The first element is the data frame
            containing the parsed results. The second element is a set
            containing all unknown cash flow types.

        """
        if statement:
            self.statement = statement

        parser = P2PParser(
            self.name, self.date_range, self.statement, header=2,
            signals=self.signals)

        # Create a new column for identifying cash flow types
        try:
            parser.df['Cash Flow Type'] = parser.df['Type'] + ' ' \
                + parser.df['Description']
        except KeyError as err:
            raise RuntimeError(_translate(
                'P2PParser',
                f'{self.name}: column {str(err)} is missing in account '
                'statement!'))

        # Define mapping between Twino and easyp2p cash flow types and column
        # names
        cashflow_types = {
            'BUYBACK INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'BUYBACK PRINCIPAL': parser.BUYBACK_PAYMENT,
            'BUY_SHARES PRINCIPAL': parser.INVESTMENT_PAYMENT,
            'CURRENCY_FLUCTUATION INTEREST': parser.INTEREST_PAYMENT,
            'EXTENSION INTEREST': parser.INTEREST_PAYMENT,
            'EXTENSION PRINCIPAL': parser.REDEMPTION_PAYMENT,
            'REPAYMENT INTEREST': parser.INTEREST_PAYMENT,
            'REPAYMENT PRINCIPAL': parser.REDEMPTION_PAYMENT,
            'REPURCHASE INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'REPURCHASE PRINCIPAL': parser.BUYBACK_PAYMENT,
            'SCHEDULE INTEREST': parser.INTEREST_PAYMENT
            }
        rename_columns = {'Processing Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%d.%m.%Y %H:%M', rename_columns, cashflow_types,
            'Cash Flow Type', 'Amount, EUR')

        return parser.df, unknown_cf_types
