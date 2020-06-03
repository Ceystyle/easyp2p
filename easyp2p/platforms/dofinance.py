# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse DoFinance statement.

"""

from typing import Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform

_translate = QCoreApplication.translate


class DoFinance(BasePlatform):

    """
    Contains methods for downloading/parsing DoFinance account statements.
    """

    NAME = 'DoFinance'
    SUFFIX = 'xlsx'
    DATE_FORMAT = '%d.%m.%Y'
    RENAME_COLUMNS = {'Processing Date': P2PParser.DATE}
    ORIG_CF_COLUMN = 'Transaction Type'
    VALUE_COLUMN = 'Amount, €'
    SKIP_FOOTER = 2

    def download_statement(self) -> None:  # pylint: disable=arguments-differ
        """
        Generate and download the DoFinance account statement for given date
        range.

        """
        login_url = 'https://www.dofinance.eu/en/users/login'
        statement_url = 'https://www.dofinance.eu/en/users/statement'
        logout_url = 'https://www.dofinance.eu/en/users/logout'
        token_names = ['_Token[fields]', '_Token[unlocked]']

        with P2PSession(self.NAME, logout_url, self.signals) as sess:
            data = sess.get_values_from_tag_by_name(
                login_url, 'input', token_names, _translate(
                    'P2PPlatform',
                    f'{self.NAME}: loading login page was not successful!'))
            data['_method'] = 'POST'
            sess.log_into_page(login_url, 'email', 'password', data)

            data = sess.get_values_from_tag_by_name(
                statement_url, 'input', token_names, _translate(
                    'P2PPlatform',
                    f'{self.NAME}: loading account statement page was not '
                    f'successful!'))
            data['_method'] = 'PUT'
            data['date_from'] = self.date_range[0].strftime('%d.%m.%Y')
            data['date_to'] = self.date_range[1].strftime('%d.%m.%Y')
            data['trans_type'] = ''
            data['xls'] = 'Download+XLS'
            sess.download_statement(statement_url, self.statement, 'post', data)

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for DoFinance.

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
            self.NAME, self.date_range, self.statement,
            skipfooter=self.SKIP_FOOTER, signals=self.signals)

        # Define mapping between DoFinance and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Profit': parser.INTEREST_PAYMENT,
            # treat bonus payments as interest payments
            'Investor Bonus': parser.INTEREST_PAYMENT}

        for cf_type in parser.df[self.ORIG_CF_COLUMN].unique():
            if cf_type.startswith('Repayment'):
                cashflow_types[cf_type] = parser.REDEMPTION_PAYMENT
            elif cf_type.startswith('Investment'):
                cashflow_types[cf_type] = parser.INVESTMENT_PAYMENT
            elif cf_type.startswith('Funding'):
                cashflow_types[cf_type] = parser.IN_OUT_PAYMENT

        unknown_cf_types = parser.parse(
            self.DATE_FORMAT, self.RENAME_COLUMNS, cashflow_types,
            self.ORIG_CF_COLUMN, self.VALUE_COLUMN)

        return parser.df, unknown_cf_types
