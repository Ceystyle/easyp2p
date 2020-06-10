# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Bondora statement.

"""

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform


class Bondora(BasePlatform):

    """Contains methods for downloading/parsing Bondora account statements."""

    NAME = 'Bondora'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    LOGIN_URL = 'https://www.bondora.com/en/login/'
    LOGOUT_URL = 'https://www.bondora.com/en/authorize/logout/'

    # Parser settings
    DATE_FORMAT = '%d.%m.%Y'
    RENAME_COLUMNS = {
        'Closing balance': P2PParser.END_BALANCE_NAME,
        'Interest received - total': P2PParser.INTEREST_PAYMENT,
        'Net capital deployed': P2PParser.IN_OUT_PAYMENT,
        'Net loan investments': P2PParser.INVESTMENT_PAYMENT,
        'Period': P2PParser.DATE,
        'Principal received - total': P2PParser.REDEMPTION_PAYMENT,
        'Opening balance': P2PParser.START_BALANCE_NAME,
    }

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the Bondora account statement for given date
        range.

        Args:
            sess: P2PSession instance.

        """
        token_field = '__RequestVerificationToken'
        data = sess.get_values_from_tag_by_name(
            self.LOGIN_URL, 'input', [token_field],
            self.errors.load_login_failed)

        sess.log_into_page(self.LOGIN_URL, 'Email', 'Password', data)

        dates = {
            'StartYear': self.date_range[0].strftime('%Y'),
            'StartMonth': self.date_range[0].strftime('%-m'),
            'EndYear': self.date_range[1].strftime('%Y'),
            'EndMonth': self.date_range[1].strftime('%-m'),
        }
        url = 'https://www.bondora.com/en/cashflow/searchcashflow?'
        for key, value in dates.items():
            url += str(key) + '=' + str(value) + '&'
        url += 'downloadExcel=true'
        sess.download_statement(url, self.statement, 'get')

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Include column with the defaulted payments.

        Args:
            parser: P2PParser instance.

        """
        parser.df[parser.DEFAULTS] = (
            parser.df['Principal received - total']
            - parser.df['Principal planned - total'])
