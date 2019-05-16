# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module with statement download tests for all supported P2P platforms."""

from datetime import date
import os
import tempfile
from typing import Tuple
import unittest

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import get_df_from_file
from easyp2p.p2p_webdriver import P2PWebDriver
import easyp2p.platforms as p2p_platforms
from tests import RESULT_PREFIX, TEST_PREFIX, PLATFORMS


@unittest.skipIf(
    input('Run download tests (y/n)?: ').lower() != 'y',
    'Download tests skipped!')
class BaseDownloadTests(unittest.TestCase):

    """
    Class providing functionality for running the statement download tests.
    """

    def setUp(self) -> None:
        """Dummy setUp, needs to be overridden by child classes."""
        self.name = None
        self.Platform = None

    def run_download_test(
            self, result_file: str, date_range: Tuple[date, date],
            header: int = 0) -> None:
        """
        Download platform account statement and compare it to result_file.

        Args:
            result_file: File with expected results without prefix or suffix.
            date_range: Date range for which to generate the account statement.
            header: Row number to use as column names and start of data for
                comparing downloaded statement to expected result.

        """
        if self.name is None or self.Platform is None:
            self.skipTest('No name or platform class provided!')

        expected_results = \
            RESULT_PREFIX + result_file + '.' + PLATFORMS[self.name]
        statement_without_suffix = TEST_PREFIX + result_file

        if not os.path.isfile(expected_results):
            self.skipTest(
                'Expected results file {} not found!'.format(
                    expected_results))

        credentials = get_credentials(self.name, ask_user=False)
        if credentials is (None, None):
            self.skipTest(
                'No credentials for {} in the keyring.'.format(self.name))

        platform = self.Platform(date_range, statement_without_suffix)

        # For now we just test in non-headless mode
        with tempfile.TemporaryDirectory() as download_directory:
            with P2PWebDriver(download_directory, False) as driver:
                platform.download_statement(driver, credentials)

        self.assertTrue(
            are_files_equal(
                platform.statement, expected_results, header=header))


class BondoraDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for Bondora."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Bondora'
        self.Platform = p2p_platforms.Bondora

    def test_download_statement(self) -> None:
        self.run_download_test('download_bondora_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_bondora_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class DoFinanceDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for DoFinance."""

    DATE_RANGE = (date(2018, 5, 1), date(2018, 8, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'DoFinance'
        self.Platform = p2p_platforms.DoFinance

    def test_download_statement(self) -> None:
        self.run_download_test('download_dofinance_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_dofinance_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class EstateguruDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for Estateguru."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Estateguru'
        self.Platform = p2p_platforms.Estateguru

    def test_download_statement(self) -> None:
        self.run_download_test('download_estateguru_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_estateguru_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class GrupeerDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for Grupeer."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Grupeer'
        self.Platform = p2p_platforms.Grupeer

    def test_download_statement(self) -> None:
        self.run_download_test('download_grupeer_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_grupeer_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class IuvoDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for Iuvo."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Iuvo'
        self.Platform = p2p_platforms.Iuvo

    def test_download_statement(self) -> None:
        self.run_download_test('download_iuvo_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_iuvo_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class MintosDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for Mintos."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Mintos'
        self.Platform = p2p_platforms.Mintos

    def test_download_statement(self) -> None:
        self.run_download_test('download_mintos_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_mintos_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class PeerBerryDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for PeerBerry."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'PeerBerry'
        self.Platform = p2p_platforms.PeerBerry

    def test_download_statement(self) -> None:
        self.run_download_test('download_peerberry_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_peerberry_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class RobocashDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for Robocash."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Robocash'
        self.Platform = p2p_platforms.Robocash

    def test_download_statement(self) -> None:
        self.run_download_test('download_robocash_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_robocash_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class SwaperDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for PeerBerry."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Swaper'
        self.Platform = p2p_platforms.Swaper

    def test_download_statement(self) -> None:
        self.run_download_test('download_swaper_statement', self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_swaper_statement_no_cfs', self.DATE_RANGE_NO_CFS)


class TwinoDownloadTests(BaseDownloadTests):

    """Class containing the statement download tests for PeerBerry."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Twino'
        self.Platform = p2p_platforms.Twino

    def test_download_statement(self) -> None:
        self.run_download_test(
            'download_twino_statement', self.DATE_RANGE, header=2)

    def test_download_statement_no_cfs(self) -> None:
        self.run_download_test(
            'download_twino_statement_no_cfs', self.DATE_RANGE_NO_CFS, header=2)


def are_files_equal(
        file1: str, file2: str, header: int = 0) -> bool:
    """
    Function to determine if two files containing pd.DataFrames are equal.

    Args:
        file1: Name including path of first file.
        file2: Name including path of second file.
        header: Row number to use as column names and start of data.

    Returns:
        bool: True if the files are equal, False if not or if at least one
        of the files does not exist.

    """
    try:
        df1 = get_df_from_file(file1, header=header)
        df2 = get_df_from_file(file2, header=header)
    except RuntimeError as err:
        print('File not found: ', err)
        return False

    return df1.equals(df2)


if __name__ == '__main__':
    unittest.main()
