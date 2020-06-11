#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Viventor statement.

"""

import json

import pandas as pd

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform


class Viventor(BasePlatform):

    """
    Contains methods for downloading/parsing Viventor account statements.
    """

    NAME = 'Viventor'
    SUFFIX = 'json'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    JSON = True
    LOGIN_URL = 'https://api.viventor.com/api/ia/clients/authentication'
    LOGOUT_URL = 'https://www.viventor.com/logout'
    STATEMENT_URL = 'https://api.viventor.com/api/app/v1/myaccounts.json'

    # Parser settings
    DATE_FORMAT = '%Y-%m-%d'
    RENAME_COLUMNS = {'date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'BUY_NOTE': P2PParser.INVESTMENT_PAYMENT,
        'BUYBACK_FEE': P2PParser.LATE_FEE_PAYMENT,
        'BUYBACK_INTEREST': P2PParser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK_PRINCIPAL': P2PParser.BUYBACK_PAYMENT,
        'DEPOSIT': P2PParser.IN_OUT_PAYMENT,
        'REPAYMENT_INTEREST': P2PParser.INTEREST_PAYMENT,
        'REPAYMENT_FEE': P2PParser.LATE_FEE_PAYMENT,
        'REPAYMENT_PRINCIPAL': P2PParser.REDEMPTION_PAYMENT,
    }
    ORIG_CF_COLUMN = 'type'
    VALUE_COLUMN = 'amount'
    BALANCE_COLUMN = 'residual'

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the Viventor account statement for given date
        range.

        Args:
            sess: P2PSession instance.

        """
        data = {'web': 'true'}
        resp = sess.log_into_page(self.LOGIN_URL, 'email', 'password', data)
        access_token = json.loads(resp.text)['token']
        sess.sess.headers.update(
            {'Authorization': f'Bearer {access_token}'})

        data = {
            'start_date': self.date_range[0].strftime(self.DATE_FORMAT),
            'end_date': self.date_range[1].strftime(self.DATE_FORMAT),
            'payment_type': 0
        }
        sess.download_statement(
            self.STATEMENT_URL, self.statement, 'post', data)

    def _transform_df(self, parser: P2PParser) -> None:
        parser.df = pd.json_normalize(parser.df['results'])
        if not parser.df.empty:
            parser.df[self.VALUE_COLUMN] = \
                parser.df[self.VALUE_COLUMN].fillna(0) \
                + parser.df['fundsInTransit'].fillna(0)
