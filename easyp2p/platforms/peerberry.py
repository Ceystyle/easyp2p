#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse PeerBerry statement.

"""

import json

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform


class PeerBerry(BasePlatform):

    """
    Contains methods for downloading/parsing PeerBerry account statements.
    """

    NAME = 'PeerBerry'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    LOGIN_URL = 'https://api.peerberry.com/v1/investor/login'
    LOGOUT_URL = 'https://api.peerberry.com/v1/investor/logout'

    # Parser settings
    DATE_FORMAT = '%Y-%m-%d'
    RENAME_COLUMNS = {
        'Currency': P2PParser.CURRENCY,
        'Date': P2PParser.DATE,
    }
    CASH_FLOW_TYPES = {
        'BUYBACK_INTEREST': P2PParser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK_PRINCIPAL': P2PParser.BUYBACK_PAYMENT,
        'INVESTMENT': P2PParser.INVESTMENT_PAYMENT,
        'REPAYMENT_INTEREST': P2PParser.INTEREST_PAYMENT,
        'REPAYMENT_PRINCIPAL': P2PParser.REDEMPTION_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Type'
    VALUE_COLUMN = 'Amount'

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the PeerBerry account statement for given date
        range.

        Args:
            sess: P2PSession instance.

        """
        resp = sess.log_into_page(self.LOGIN_URL, 'email', 'password')
        access_token = json.loads(resp.text)['access_token']
        sess.sess.headers.update(
            {'Authorization': f'Bearer {access_token}'})
        statement_url = (
            f'https://api.peerberry.com/v1/investor/transactions/import?'
            f'startDate={self.date_range[0].strftime("%Y-%m-%d")}&'
            f'endDate={self.date_range[1].strftime("%Y-%m-%d")}&'
            f'transactionType=0&lang=en')
        sess.download_statement(statement_url, self.statement, 'get')
