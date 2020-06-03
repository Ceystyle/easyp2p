# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Bondora statement.

"""

from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform

_translate = QCoreApplication.translate


class Bondora(BasePlatform):

    """Contains methods for downloading/parsing Bondora account statements."""

    NAME = 'Bondora'
    SUFFIX = 'xlsx'
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

    def download_statement(self) -> None:  # pylint: disable=arguments-differ
        """
        Generate and download the Bondora account statement for given date
        range.

        """
        login_url = 'https://www.bondora.com/en/login/'
        logout_url = 'https://www.bondora.com/en/authorize/logout/'

        with P2PSession(self.NAME, logout_url, self.signals) as sess:
            token_field = '__RequestVerificationToken'
            data = sess.get_values_from_tag_by_name(
                login_url, 'input', [token_field], _translate(
                    'P2PPlatform',
                    f'{self.NAME}: loading login page was not successful!'))

            sess.log_into_page(login_url, 'Email', 'Password', data)

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
