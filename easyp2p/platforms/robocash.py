# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Robocash statement.

"""

import json

from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform

_translate = QCoreApplication.translate


class Robocash(BasePlatform):

    """
    Contains methods for downloading/parsing Robocash account statements.
    """

    NAME = 'Robocash'
    SUFFIX = 'xls'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'

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

    def _session_download(self) -> None:
        """
        Generate and download the Robocash account statement for given date
        range.

        """
        login_url = 'https://robo.cash/login'
        logout_url = 'https://robo.cash/logout'
        gen_statement_url = 'https://robo.cash/cabinet/statement/generate'
        statement_url = 'https://robo.cash/cabinet/statement'

        with P2PSession(self.NAME, logout_url, self.signals) as sess:
            data = sess.get_values_from_tag_by_name(
                login_url, 'input', ['_token'], _translate(
                    'P2PPlatform',
                    f'{self.NAME}: loading website was not successful!'))
            sess.log_into_page(login_url, 'email', 'password', data=data)

            statement_err_msg = _translate(
                'P2PPlatform',
                f'{self.NAME}: loading the account statement page failed!')
            token = sess.get_value_from_script(
                statement_url, {'id': 'report-template'}, 'input', '_token',
                statement_err_msg)

            data = {
                '_token': token,
                'currency_id': '1',
                'start_date': self.date_range[0].strftime("%Y-%m-%d"),
                'end_date': self.date_range[1].strftime("%Y-%m-%d"),
                'statement_type': '1'
            }
            sess.generate_account_statement(gen_statement_url, 'post', data)

            def download_ready():
                report = json.loads(sess.get_value_from_tag(
                    statement_url, 'report-component', ':initial_report',
                    statement_err_msg))
                if report['filename'] is not None:
                    sess.download_statement(
                        f'https://robo.cash/cabinet/statement/{report["id"]}'
                        f'/download', self.statement, 'get')
                    return True
                return False

            sess.wait(download_ready)
