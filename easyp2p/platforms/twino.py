# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Twino statement.

"""

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.p2p_signals import PlatformFailedError
from easyp2p.platforms.base_platform import BasePlatform


class Twino(BasePlatform):

    """
    Contains methods for downloading/parsing Twino account statements.
    """

    NAME = 'Twino'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    JSON = True
    LOGIN_URL = 'https://www.twino.eu/ws/public/login2fa'
    LOGOUT_URL = 'https://www.twino.eu/logout'
    GEN_STATEMENT_URL = \
        'https://www.twino.eu/ws/web/investor/account-entries/' \
        'init-export-to-excel'

    # Parser settings
    DATE_FORMAT = '%d.%m.%Y %H:%M'
    RENAME_COLUMNS = {'Processing Date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'BUYBACK INTEREST': P2PParser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK PRINCIPAL': P2PParser.BUYBACK_PAYMENT,
        'BUY_SHARES PRINCIPAL': P2PParser.INVESTMENT_PAYMENT,
        'CURRENCY_FLUCTUATION INTEREST': P2PParser.INTEREST_PAYMENT,
        'EXTENSION INTEREST': P2PParser.INTEREST_PAYMENT,
        'EXTENSION PRINCIPAL': P2PParser.REDEMPTION_PAYMENT,
        'REPAYMENT INTEREST': P2PParser.INTEREST_PAYMENT,
        'REPAYMENT PRINCIPAL': P2PParser.REDEMPTION_PAYMENT,
        'REPURCHASE INTEREST': P2PParser.BUYBACK_INTEREST_PAYMENT,
        'REPURCHASE PRINCIPAL': P2PParser.BUYBACK_PAYMENT,
        'SCHEDULE INTEREST': P2PParser.INTEREST_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Cash Flow Type'
    VALUE_COLUMN = 'Amount, EUR'
    HEADER = 2

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the Twino account statement for given date range.

        Args:
            sess: P2PSession instance.

        Raises:
            PlatformFailedError: If two factor authorization is enabled.

        """
        # FIXME: do not ask user twice for credentials if they are not in the
        # keyring
        username = get_credentials(self.NAME, self.signals)[0]
        check2fa_url = (
            f'https://www.twino.eu/ws/public/check2fa?email={username}')
        resp = sess.request(check2fa_url, 'get', self.errors.load_login_failed)

        if resp.json():
            raise PlatformFailedError(self.errors.tfa_not_supported)

        sess.log_into_page(self.LOGIN_URL, 'name', 'password')

        start_date = [
            self.date_range[0].year, self.date_range[0].month,
            self.date_range[0].day]
        end_date = [
            self.date_range[1].year, self.date_range[1].month,
            self.date_range[1].day]
        data = {
            'processingDateFrom': start_date,
            'processingDateTo': end_date,
        }
        sess.request(
            self.GEN_STATEMENT_URL, 'post',
            self.errors.statement_generation_failed, data)

        def download_ready():
            download_url = (
                f'https://www.twino.eu/ws/web/export-to-excel/{username}/'
                f'download')
            res = sess.request(
                download_url, 'get', self.errors.statement_download_failed,
                success_codes=(200, 500))
            if res.status_code == 200:
                with open(self.statement, 'wb') as file:
                    file.write(res.content)
                return True

            if res.status_code == 500:
                return False

            raise RuntimeError(self.errors.statement_download_failed)

        sess.wait(download_ready)

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Merge Type and Description columns to identify the cash flow types.

        Args:
            parser: P2PParser instance

        """
        parser.check_columns('Type', 'Description')
        parser.df['Cash Flow Type'] = parser.df['Type'] + ' ' \
            + parser.df['Description']
