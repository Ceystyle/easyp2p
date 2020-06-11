#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Estateguru statement.

"""

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform


class Estateguru(BasePlatform):

    """
    Contains methods for downloading/parsing Estateguru account statements.
    """

    NAME = 'Estateguru'
    SUFFIX = 'csv'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    LOGIN_URL = 'https://estateguru.co/portal/login/authenticate'
    LOGOUT_URL = 'https://estateguru.co/portal/logoff'
    STATEMENT_URL = 'https://estateguru.co/portal/portfolio/account'
    GEN_STATEMENT_URL = \
        'https://estateguru.co/portal/portfolio/ajaxFilterTransactions'

    # Parser settings
    DATE_FORMAT = '%d/%m/%Y %H:%M'
    RENAME_COLUMNS = {
        'Cash Flow Type': 'EG Cash Flow Type',
        'Confirmation Date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'Bonus': P2PParser.BONUS_PAYMENT,
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

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the Estateguru account statement for given date
        range.

        Args:
            sess: P2PSession instance.

        """
        sess.log_into_page(self.LOGIN_URL, 'username', 'password')

        download_url = sess.get_url_from_partial_link(
            self.STATEMENT_URL, 'downloadOrderReport.csv',
            self.errors.load_statement_page_failed)
        user_id = download_url.split('&')[1].split('=')[1]

        data = {
            'currentUserId': user_id,
            'currentCurrency': "EUR",
            'filter_isFilter': "[true]",
            'filterTableId': "dataTableTransaction",
            'filter_dateApproveFilterFrom':
                f"[{self.date_range[0].strftime('%d.%m.%Y')}]",
            'filter_dateApproveFilterTo':
                f"[{self.date_range[1].strftime('%d.%m.%Y')}]",
            'controller': "portfolio",
            'action': "ajaxFilterTransactions",
        }
        sess.request(
            self.GEN_STATEMENT_URL, 'post',
            self.errors.statement_generation_failed, data)

        sess.download_statement(
            f'https://estateguru.co{download_url}', self.statement, 'get')

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Only consider cash flows in status "Approved".

        Args:
            parser: P2PParser instance

        Returns:

        """
        parser.df = parser.df[parser.df['Cash Flow Status'] == 'Approved']
