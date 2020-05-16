#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Estateguru statement.

"""

from datetime import date
from typing import Optional, Tuple

from bs4 import BeautifulSoup
import pandas as pd
from PyQt5.QtCore import QCoreApplication
import requests

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class Estateguru:

    """
    Contains methods for downloading/parsing Estateguru account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Estateguru class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Estateguru'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.csv'
        self.signals = signals

    def download_statement(self, _) -> None:
        """
            Generate and download the Estateguru account statement for given date
            range.

            Args:
                _: Ignored. This is needed for consistency with platforms that
                    use WebDriver to download the statement.

            Raises:
                RuntimeError:
                    - If no credentials for Estateguru are provided.
                    - If login, loading the page, generating or downloading the
                      account statement is not successful.
                RuntimeWarning: If logout is not successful.

        """
        credentials = get_credentials(self.name, self.signals)

        with requests.session() as sess:
            data = {
                'username': credentials[0],
                'password': credentials[1],
            }
            resp = sess.post(
                'https://estateguru.co/portal/login/authenticate',
                data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform', f'{self.name}: login was not successful. '
                    'Are the credentials correct?'))
            self.signals.update_progress_bar.emit()

            resp = sess.get('https://estateguru.co/portal/portfolio/account')
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: loading account statement page was not '
                    'successful!'))
            self.signals.update_progress_bar.emit()

            soup = BeautifulSoup(resp.text, 'html.parser')
            download_url = None
            for link in soup.find_all('a', href=True):
                if 'downloadOrderReport.csv' in link['href']:
                    download_url = link['href']
            if download_url is None:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: generating the account statement was not '
                    f'successful!'))
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
            resp = sess.post(
                'https://estateguru.co/portal/portfolio/ajaxFilterTransactions',
                data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: account statement generation failed!'))
            self.signals.update_progress_bar.emit()

            resp = sess.get(f'https://estateguru.co{download_url}')
            if resp.status_code == 200:
                with open(self.statement, 'w') as file:
                    file.write(resp.text)
            else:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: download of account statement failed!'))
            self.signals.update_progress_bar.emit()

            resp = sess.get('https://estateguru.co/portal/logoff')
            if resp.status_code != 200:
                raise RuntimeWarning(_translate(
                    'P2PPlatform', f'{self.name}: logout was not successful!'))
            self.signals.update_progress_bar.emit()

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
            self.name, self.date_range, self.statement, skipfooter=1,
            signals=self.signals)

        # Only consider valid cash flows
        parser.df = parser.df[parser.df['Cash Flow Status'] == 'Approved']

        # Define mapping between Estateguru and easyp2p cash flow types and
        # column names
        cashflow_types = {
            # Treat bonus payments as normal interest payments
            'Bonus': parser.INTEREST_PAYMENT,
            'Deposit': parser.IN_OUT_PAYMENT,
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Indemnity': parser.LATE_FEE_PAYMENT,
            'Principal': parser.REDEMPTION_PAYMENT,
            'Investment(Auto Invest)': parser.INVESTMENT_PAYMENT,
            'Penalty': parser.LATE_FEE_PAYMENT,
            'Interest': parser.INTEREST_PAYMENT}
        rename_columns = {
            'Cash Flow Type': 'EG Cash Flow Type',
            'Confirmation Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%d/%m/%Y %H:%M', rename_columns, cashflow_types,
            'EG Cash Flow Type', 'Amount', 'Available to invest')

        return parser.df, unknown_cf_types
