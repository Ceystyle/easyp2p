# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing platform tests for easyp2p"""

from datetime import date
import os
import sys
from typing import Tuple
import unittest
import keyring

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../easyp2p')))
from easyp2p_tests import are_files_equal, RESULT_PREFIX
from platforms import (
    bondora, dofinance, estateguru, grupeer, iuvo, mintos, peerberry, robocash,
    swaper, twino)

class PlatformTests(unittest.TestCase):
    """Test downloading account statements from all supported platforms."""

    def setUp(self):
        """Initializes the default date ranges for the tests."""
        self.date_range = (date(2018, 9, 1), date(2018, 12, 31))
        self.date_range_no_cfs = (date(2016, 9, 1), date(2016, 12, 31))

    def get_credentials_from_keyring(self, platform: str) -> Tuple[str, str]:
        """
        Helper method to get credentials from the keyring.

        Args:
            platform (str): Name of the P2P platform

        Returns:
            Tuple[str, str]: (username, password) for the P2P platform

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
        """Test download_bondora_statement"""
        credentials = self.get_credentials_from_keyring('Bondora')
        bondora.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            RESULT_PREFIX + 'download_bondora_statement.csv'))

    def test_download_bondora_statement_no_cfs(self) -> None:
        """
        Test download_bondora_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('Bondora')
        bondora.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            RESULT_PREFIX + 'download_bondora_statement_no_cfs.csv'))

    def test_download_dofinance_statement(self):
        """Test download_dofinance_statement function"""
        credentials = self.get_credentials_from_keyring('DoFinance')
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        dofinance.download_statement(
            dofinance_date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/dofinance_statement.xlsx',
            RESULT_PREFIX + 'download_dofinance_statement.xlsx'))

    def test_download_dofinance_statement_no_cfs(self):
        """
        Test download_dofinance_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('DoFinance')
        dofinance.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/dofinance_statement.xlsx',
            RESULT_PREFIX +'download_dofinance_statement_no_cfs.xlsx'))

    def test_download_estateguru_statement(self):
        """Test download_estateguru_statement"""
        credentials = self.get_credentials_from_keyring('Estateguru')
        estateguru.download_statement(
            self.date_range, credentials)
        # The Estateguru statement contains all cashflows ever generated for
        # this account. Therefore it changes regularly and we cannot compare
        # it to a fixed reference file. This test just makes sure that the
        # statement was downloaded.
        # TODO: check for content errors
        self.assertTrue(os.path.isfile(
            'p2p_downloads/estateguru_statement.csv'))

    def test_download_grupeer_statement(self):
        """Test download_grupeer_statement"""
        credentials = self.get_credentials_from_keyring('Grupeer')
        grupeer.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/grupeer_statement.xlsx',
            RESULT_PREFIX + 'download_grupeer_statement.xlsx'))

    def test_download_grupeer_statement_no_cfs(self):
        """
        Test download_grupeer_statement if there are no cashflows in date_range
        """
        credentials = self.get_credentials_from_keyring('Grupeer')
        grupeer.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/grupeer_statement.xlsx',
            RESULT_PREFIX + 'download_grupeer_statement_no_cfs.xlsx'))

    def test_download_iuvo_statement(self):
        """Test download_iuvo_statement"""
        credentials = self.get_credentials_from_keyring('Iuvo')
        iuvo.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/iuvo_statement.xlsx',
            RESULT_PREFIX + 'download_iuvo_statement.xlsx'))

    def test_download_iuvo_statement_no_cfs(self):
        """
        Test download_iuvo_statement when there are no cashflows in
        date_range
        """
        credentials = self.get_credentials_from_keyring('Iuvo')
        iuvo.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/iuvo_statement.xlsx',
            RESULT_PREFIX + 'download_iuvo_statement_no_cfs.xlsx'))

    def test_download_mintos_statement(self):
        """Test download_mintos_statement"""
        credentials = self.get_credentials_from_keyring('Mintos')
        mintos.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/mintos_statement.xlsx',
            RESULT_PREFIX + 'download_mintos_statement.xlsx'))

    def test_download_mintos_statement_no_cfs(self):
        """
        Test download_mintos_statement when there is no cashflow in date_range
        """
        credentials = self.get_credentials_from_keyring('Mintos')
        mintos.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/mintos_statement.xlsx',
            RESULT_PREFIX + 'download_mintos_statement_no_cfs.xlsx'))

    def test_download_peerberry_statement(self):
        """Test download_peerberry_statement"""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        peerberry.download_statement(
            self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/peerberry_statement.csv',
            RESULT_PREFIX + 'download_peerberry_statement.csv'))

    def test_download_peerberry_statement_no_cfs(self):
        """
        Test download_peerberry_statement when there is no cashflow in
        date_range
        """
        credentials = self.get_credentials_from_keyring('PeerBerry')
        peerberry.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/peerberry_statement.csv',
            RESULT_PREFIX + 'download_peerberry_statement_no_cfs.csv'))

    def test_download_robocash_statement(self):
        """Test download_robocash_statement function"""
        credentials = self.get_credentials_from_keyring('Robocash')
        robocash.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/robocash_statement.xls',
            RESULT_PREFIX + 'download_robocash_statement.xls'))

    def test_download_robocash_statement_no_cfs(self):
        """
        Test download_robocash_statement function when there is no cashflow in
        date_range
        """
        credentials = self.get_credentials_from_keyring('Robocash')
        robocash.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/robocash_statement.xls',
            RESULT_PREFIX + 'download_robocash_statement_no_cfs.xls'))

    def test_download_swaper_statement(self):
        """Test download_swaper_statement function"""
        credentials = self.get_credentials_from_keyring('Swaper')
        swaper.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/swaper_statement.xlsx',
            RESULT_PREFIX + 'download_swaper_statement.xlsx'))

    def test_download_swaper_statement_no_cfs(self) -> None:
        """
        Test download_swaper_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('Swaper')
        swaper.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/swaper_statement.xlsx',
            RESULT_PREFIX + 'download_swaper_statement_no_cfs.xlsx'))

    def test_download_twino_statement(self):
        """Test download_twino_statement"""
        credentials = self.get_credentials_from_keyring('Twino')
        twino.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/twino_statement.xlsx',
            RESULT_PREFIX + 'download_twino_statement.xlsx',
            drop_header=True))

    def test_download_twino_statement_no_cfs(self):
        """
        Test download_twino_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('Twino')
        twino.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/twino_statement.xlsx',
            RESULT_PREFIX + 'download_twino_statement_no_cfs.xlsx',
            drop_header=True))

if __name__ == '__main__':
    unittest.main()
