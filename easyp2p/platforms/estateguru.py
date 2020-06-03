#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Estateguru statement.

"""

from typing import Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform

_translate = QCoreApplication.translate


class Estateguru(BasePlatform):

    """
    Contains methods for downloading/parsing Estateguru account statements.
    """

    NAME = 'Estateguru'
    SUFFIX = 'csv'
    DATE_FORMAT = '%d/%m/%Y %H:%M'
    RENAME_COLUMNS = {
        'Cash Flow Type': 'EG Cash Flow Type',
        'Confirmation Date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        # Treat bonus payments as normal interest payments
        'Bonus': P2PParser.INTEREST_PAYMENT,
        'Deposit': P2PParser.IN_OUT_PAYMENT,
        'Withdrawal': P2PParser.IN_OUT_PAYMENT,
        'Indemnity': P2PParser.LATE_FEE_PAYMENT,
        'Principal': P2PParser.REDEMPTION_PAYMENT,
        'Investment(Auto Invest)': P2PParser.INVESTMENT_PAYMENT,
        'Penalty': P2PParser.LATE_FEE_PAYMENT,
        'Interest': P2PParser.INTEREST_PAYMENT,
    }
    ORIG_CF_COLUMN = 'EG Cash Flow Type'
    VALUE_COLUMN = 'Amount'
    BALANCE_COLUMN = 'Available to invest'
    SKIP_FOOTER = 1

    def download_statement(self) -> None:  # pylint: disable=arguments-differ
        """
        Generate and download the Estateguru account statement for given date
        range.

        """
        login_url = 'https://estateguru.co/portal/login/authenticate'
        logout_url = 'https://estateguru.co/portal/logoff'
        statement_url = 'https://estateguru.co/portal/portfolio/account'
        gen_statement_url = (
            'https://estateguru.co/portal/portfolio/ajaxFilterTransactions')

        with P2PSession(self.NAME, logout_url, self.signals) as sess:
            sess.log_into_page(login_url, 'username', 'password')

            download_url = sess.get_url_from_partial_link(
                statement_url, 'downloadOrderReport.csv', _translate(
                    'P2PPlatform',
                    f'{self.NAME}: loading account statement page failed!'))
            user_id = download_url.split('&')[1].split('=')[1]

            data = {
                'currentUserId': user_id,
                'currentCurrency': "EUR",
                'userDetails': "",
                'showFutureTransactions': "false",
                'order': "",
                'sort': "",
                'filter_isFilter': "[true]",
                'filterTableId': "dataTableTransaction",
                'filter_dateApproveFilterFrom':
                    f"[{self.date_range[0].strftime('%d.%m.%Y')}]",
                'filter_dateApproveFilterTo':
                    f"[{self.date_range[1].strftime('%d.%m.%Y')}]",
                'filter_loanName': "",
                'controller': "portfolio",
                'format': "null",
                'action': "ajaxFilterTransactions",
                'max': "20",
                'offset': "40"
            }
            sess.generate_account_statement(gen_statement_url, 'post', data)

            sess.download_statement(
                f'https://estateguru.co{download_url}', self.statement, 'get')

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Estateguru.

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

        # Only consider valid cash flows
        parser.df = parser.df[parser.df['Cash Flow Status'] == 'Approved']

        unknown_cf_types = parser.parse(
            self.DATE_FORMAT, self.RENAME_COLUMNS, self.CASH_FLOW_TYPES,
            self.ORIG_CF_COLUMN, self.VALUE_COLUMN, self.BALANCE_COLUMN)

        return parser.df, unknown_cf_types
