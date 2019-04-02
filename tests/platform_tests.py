# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all account statement download tests for easyp2p."""

from datetime import date
import os
from typing import Tuple
import unittest
import keyring

from tests.parser_tests import are_files_equal, RESULT_PREFIX
from tests.context import p2p_platforms


class PlatformTests(unittest.TestCase):

    """Test downloading account statements from all supported platforms."""

    def setUp(self):
        """Initialize the default date ranges for the tests."""
        self.date_range = (date(2018, 9, 1), date(2018, 12, 31))
        self.date_range_no_cfs = (date(2016, 9, 1), date(2016, 12, 31))

    def get_credentials_from_keyring(self, platform: str) -> Tuple[str, str]:
        """
        Helper method to get credentials from the keyring.

        Args:
            platform: Name of the P2P platform

        Returns:
            Tuple (username, password) for the P2P platform

        """
        if keyring.get_keyring():
            try:
                username = keyring.get_password(platform, 'username')
                password = keyring.get_password(platform, username)
            except TypeError:
                self.skipTest(
                    'No credentials for {0} in the keyring.'.format(platform))

        return (username, password)

    def test_download_bondora_statement(self) -> None:
        """Test download_bondora_statement."""
        credentials = self.get_credentials_from_keyring('Bondora')
        bondora = Bondora(self.date_range)
        bondora.download_statement(credentials)
        self.assertTrue(are_files_equal(
            bondora.statement_file_name,
            RESULT_PREFIX + 'download_bondora_statement.csv'))

    def test_download_bondora_statement_no_cfs(self) -> None:
        """Test Bondora download when there are no cashflows."""
        credentials = self.get_credentials_from_keyring('Bondora')
        bondora = Bondora(self.date_range_no_cfs)
        bondora.download_statement(credentials)
        self.assertTrue(are_files_equal(
            bondora.statement_file_name,
            RESULT_PREFIX + 'download_bondora_statement_no_cfs.csv'))

    def test_download_dofinance_statement(self):
        """Test download_dofinance_statement function."""
        credentials = self.get_credentials_from_keyring('DoFinance')
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        dofinance = DoFinance(dofinance_date_range)
        dofinance.download_statement(credentials)
        self.assertTrue(are_files_equal(
            dofinance.statement_file_name,
            RESULT_PREFIX + 'download_dofinance_statement.xlsx'))

    def test_download_dofinance_statement_no_cfs(self):
        """Test DoFinance download when there are no cashflows."""
        credentials = self.get_credentials_from_keyring('DoFinance')
        dofinance = DoFinance(self.date_range_no_cfs)
        dofinance.download_statement(credentials)
        self.assertTrue(are_files_equal(
            dofinance.statement_file_name,
            RESULT_PREFIX + 'download_dofinance_statement_no_cfs.xlsx'))

    def test_download_estateguru_statement(self):
        """Test download_estateguru_statement."""
        credentials = self.get_credentials_from_keyring('Estateguru')
        estateguru = Estateguru(self.date_range_no_cfs)
        estateguru.download_statement(credentials)
        # The Estateguru statement contains all cashflows ever generated for
        # this account. Therefore it changes regularly and we cannot compare
        # it to a fixed reference file. This test just makes sure that the
        # statement was downloaded.
        # TODO: check for content errors
        self.assertTrue(os.path.isfile(estateguru.statement_file_name))

    def test_download_grupeer_statement(self):
        """Test download_grupeer_statement."""
        credentials = self.get_credentials_from_keyring('Grupeer')
        grupeer = Grupeer(self.date_range)
        grupeer.download_statement(credentials)
        self.assertTrue(are_files_equal(
            grupeer.statement_file_name,
            RESULT_PREFIX + 'download_grupeer_statement.xlsx'))

    def test_download_grupeer_statement_no_cfs(self):
        """Test Grupeer download when there are no cashflows in date_range."""
        credentials = self.get_credentials_from_keyring('Grupeer')
        grupeer = Grupeer(self.date_range_no_cfs)
        grupeer.download_statement(credentials)
        self.assertTrue(are_files_equal(
            grupeer.statement_file_name,
            RESULT_PREFIX + 'download_grupeer_statement_no_cfs.xlsx'))

    def test_download_iuvo_statement(self):
        """Test download_iuvo_statement."""
        credentials = self.get_credentials_from_keyring('Iuvo')
        iuvo = Iuvo(self.date_range)
        iuvo.download_statement(credentials)
        self.assertTrue(are_files_equal(
            iuvo.statement_file_name,
            RESULT_PREFIX + 'download_iuvo_statement.xlsx'))

    def test_download_iuvo_statement_no_cfs(self):
        """Test Iuvo download when there are no cashflows in date_range."""
        credentials = self.get_credentials_from_keyring('Iuvo')
        iuvo = Iuvo(self.date_range_no_cfs)
        iuvo.download_statement(credentials)
        self.assertTrue(are_files_equal(
            iuvo.statement_file_name,
            RESULT_PREFIX + 'download_iuvo_statement_no_cfs.xlsx'))

    def test_download_mintos_statement(self):
        """Test download_mintos_statement."""
        credentials = self.get_credentials_from_keyring('Mintos')
        mintos = Mintos(self.date_range)
        mintos.download_statement(credentials)
        self.assertTrue(are_files_equal(
            mintos.statement_file_name,
            RESULT_PREFIX + 'download_mintos_statement.xlsx'))

    def test_download_mintos_statement_no_cfs(self):
        """Test Mintos download when there are no cashflows."""
        credentials = self.get_credentials_from_keyring('Mintos')
        mintos = Mintos(self.date_range_no_cfs)
        mintos.download_statement(credentials)
        self.assertTrue(are_files_equal(
            mintos.statement_file_name,
            RESULT_PREFIX + 'download_mintos_statement_no_cfs.xlsx'))

    def test_download_peerberry_statement(self):
        """Test download_peerberry_statement."""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        peerberry = PeerBerry(self.date_range)
        peerberry.download_statement(credentials)
        self.assertTrue(are_files_equal(
            peerberry.statement_file_name,
            RESULT_PREFIX + 'download_peerberry_statement.csv'))

    def test_download_peerberry_statement_no_cfs(self):
        """Test Peerberry download when there are no cashflows."""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        peerberry = PeerBerry(self.date_range_no_cfs)
        peerberry.download_statement(credentials)
        self.assertTrue(are_files_equal(
            peerberry.statement_file_name,
            RESULT_PREFIX + 'download_peerberry_statement_no_cfs.csv'))

    def test_download_robocash_statement(self):
        """Test download_robocash_statement function."""
        credentials = self.get_credentials_from_keyring('Robocash')
        robocash = Robocash(self.date_range)
        robocash.download_statement(credentials)
        self.assertTrue(are_files_equal(
            robocash.statement_file_name,
            RESULT_PREFIX + 'download_robocash_statement.xls'))

    def test_download_robocash_statement_no_cfs(self):
        """Test Robocash download when there are no cashflows in date_range."""
        credentials = self.get_credentials_from_keyring('Robocash')
        robocash = Robocash(self.date_range_no_cfs)
        robocash.download_statement(credentials)
        self.assertTrue(are_files_equal(
            robocash.statement_file_name,
            RESULT_PREFIX + 'download_robocash_statement_no_cfs.xls'))

    def test_download_swaper_statement(self):
        """Test download_swaper_statement function."""
        credentials = self.get_credentials_from_keyring('Swaper')
        swaper = Swaper(self.date_range)
        swaper.download_statement(credentials)
        self.assertTrue(are_files_equal(
            swaper.statement_file_name,
            RESULT_PREFIX + 'download_swaper_statement.xlsx'))

    def test_download_swaper_statement_no_cfs(self) -> None:
        """Test Swaper download when there are no cashflows."""
        credentials = self.get_credentials_from_keyring('Swaper')
        swaper = Swaper(self.date_range_no_cfs)
        swaper.download_statement(credentials)
        self.assertTrue(are_files_equal(
            swaper.statement_file_name,
            RESULT_PREFIX + 'download_swaper_statement_no_cfs.xlsx'))

    def test_download_twino_statement(self):
        """Test download_twino_statement."""
        credentials = self.get_credentials_from_keyring('Twino')
        twino = Twino(self.date_range)
        twino.download_statement(credentials)
        self.assertTrue(are_files_equal(
            twino.statement_file_name,
            RESULT_PREFIX + 'download_twino_statement.xlsx',
            drop_header=True))

    def test_download_twino_statement_no_cfs(self):
        """Test Twino download when there are no cashflows."""
        credentials = self.get_credentials_from_keyring('Twino')
        twino = Twino(self.date_range_no_cfs)
        twino.download_statement(credentials)
        self.assertTrue(are_files_equal(
            twino.statement_file_name,
            RESULT_PREFIX + 'download_twino_statement_no_cfs.xlsx',
            drop_header=True))


if __name__ == '__main__':
    unittest.main()
