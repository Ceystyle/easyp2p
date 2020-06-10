# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Robocash statement.

"""

import json

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform


class Robocash(BasePlatform):

    """
    Contains methods for downloading/parsing Robocash account statements.
    """

    NAME = 'Robocash'
    SUFFIX = 'xls'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    LOGIN_URL = 'https://robo.cash/login'
    LOGOUT_URL = 'https://robo.cash/logout'
    GEN_STATEMENT_URL = 'https://robo.cash/cabinet/statement/generate'
    STATEMENT_URL = 'https://robo.cash/cabinet/statement'

    # Parser settings
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    RENAME_COLUMNS = {'Date and time': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'Adding funds': P2PParser.IN_OUT_PAYMENT,
        'Paying interest': P2PParser.INTEREST_PAYMENT,
        'Purchasing a loan': P2PParser.INVESTMENT_PAYMENT,
        'Returning a loan': P2PParser.REDEMPTION_PAYMENT,
        'Withdrawal of funds': P2PParser.IN_OUT_PAYMENT,
        # We don't report cash transfers within Robocash:
        'Creating a portfolio': P2PParser.IGNORE,
        'Refilling a portfolio': P2PParser.IGNORE,
        'Withdrawing from a portfolio': P2PParser.IGNORE,
    }
    ORIG_CF_COLUMN = 'Operation'
    VALUE_COLUMN = 'Amount'
    BALANCE_COLUMN = "Portfolio's balance"

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the Robocash account statement for given date
        range.

        Args:
            sess: P2PSession instance.

        """
        data = sess.get_values_from_tag_by_name(
            self.LOGIN_URL, 'input', ['_token'], self.errors.load_login_failed)
        sess.log_into_page(self.LOGIN_URL, 'email', 'password', data=data)

        token = sess.get_value_from_script(
            self.STATEMENT_URL, {'id': 'report-template'}, 'input',
            '_token', self.errors.load_statement_page_failed)

        data = {
            '_token': token,
            'currency_id': '1',
            'start_date': self.date_range[0].strftime("%Y-%m-%d"),
            'end_date': self.date_range[1].strftime("%Y-%m-%d"),
            'statement_type': '1'
        }
        sess.request(
            self.GEN_STATEMENT_URL, 'post',
            self.errors.statement_generation_failed, data)

        def download_ready():
            report = json.loads(sess.get_value_from_tag(
                self.STATEMENT_URL, 'report-component', ':initial_report',
                self.errors.load_statement_page_failed))
            if report['filename'] is not None:
                sess.download_statement(
                    f'https://robo.cash/cabinet/statement/{report["id"]}'
                    f'/download', self.statement, 'get')
                return True
            return False

        sess.wait(download_ready)
