#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Viventor statement.

"""

import pandas as pd

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.platforms.base_platform import BasePlatform


class Viainvest(BasePlatform):
    """
    Contains methods for downloading/parsing Viainvest account statements.
    """

    NAME = 'Viainvest'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'session'
    LOGIN_URL = 'https://viainvest.com/users/login'
    LOGOUT_URL = 'https://viainvest.com/en/users/logout'

    # Parser settings
    DATE_FORMAT = '%m/%d/%Y'
    RENAME_COLUMNS = {'Value date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'Amount invested in loan': P2PParser.INVESTMENT_PAYMENT,
        'Amount of interest payment received': P2PParser.INTEREST_PAYMENT,
        'Amount of funds deposited': P2PParser.IN_OUT_PAYMENT,
        'Amount of principal repayment received': P2PParser.REDEMPTION_PAYMENT,
        # Treat withholding tax payments as negative interest payments
        'Amount of Withholding Tax deducted': P2PParser.INTEREST_PAYMENT,
        'Correction of amount of Withholding Tax deducted':
            P2PParser.INTEREST_PAYMENT,
        'VIACONTO.se Cashback bonus payment received': P2PParser.BONUS_PAYMENT,
        'VIASMS.pl Cashback bonus payment received': P2PParser.BONUS_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Transaction type'
    VALUE_COLUMN = 'Amount'

    def _session_download(self, sess: P2PSession) -> None:
        """
        Generate and download the Viainvest account statement for given date
        range.

        Args:
            sess: P2PSession instance.

        """
        token_names = [
            'data[_Token][key]', 'data[_Token][fields]',
            'data[_Token][unlocked]']
        data = sess.get_values_from_tag_by_name(
            self.LOGIN_URL, 'input', token_names, self.errors.load_login_failed)
        data['_method'] = 'POST'
        data['data[User][is_remember]'] = '0'
        sess.log_into_page(
            self.LOGIN_URL, 'data[User][email]', 'data[User][passwd]', data)

        download_url = (
            f'https://viainvest.com/en/transactions/index/do_report/'
            f'from_date:{self.date_range[0].strftime("%Y-%m-%d")}/'
            f'to_date:{self.date_range[1].strftime("%Y-%m-%d")}')
        resp = sess.request(
            download_url, 'get', self.errors.statement_download_failed)

        # If there no cash flows in date range the website returns a HTML
        # document. Write an empty dataframe to the file in this case.
        if resp.text.startswith('<!DOCTYPE html>'):
            df = pd.DataFrame()
            df.to_excel(self.statement)
        else:
            with open(self.statement, 'bw') as file:
                file.write(resp.content)

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Merge the credit and debit columns into a single amount column.

        Args:
            parser: P2PParser instance.

        """
        for col in ('Credit (€)', 'Debit (€)'):
            if col not in parser.df.columns:
                return
            parser.df[col].fillna(0, inplace=True)
        parser.df[self.VALUE_COLUMN] = \
            parser.df['Credit (€)'] - parser.df['Debit (€)']
