# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse DoFinance statement.

"""

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

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Dynamically generate the DoFinance cash flow types.

        Args:
            parser: P2PParser instance.

        """
        cash_flow_types = {
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Profit': parser.INTEREST_PAYMENT,
            # treat bonus payments as interest payments
            'Investor Bonus': parser.INTEREST_PAYMENT,
        }

        for cf_type in parser.df[self.ORIG_CF_COLUMN].unique():
            if cf_type.startswith('Repayment'):
                cash_flow_types[cf_type] = parser.REDEMPTION_PAYMENT
            elif cf_type.startswith('Investment'):
                cash_flow_types[cf_type] = parser.INVESTMENT_PAYMENT
            elif cf_type.startswith('Funding'):
                cash_flow_types[cf_type] = parser.IN_OUT_PAYMENT

        self.CASH_FLOW_TYPES = cash_flow_types  # pylint: disable=invalid-name
