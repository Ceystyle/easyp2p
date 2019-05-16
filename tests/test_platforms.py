# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module with statement download tests for all supported P2P platforms."""

from datetime import date
import os
import tempfile
from typing import Tuple
import unittest

import pandas as pd

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import get_df_from_file
from easyp2p.p2p_webdriver import P2PWebDriver
import easyp2p.platforms as p2p_platforms
from tests import INPUT_PREFIX, PLATFORMS, RESULT_PREFIX, TEST_PREFIX

SKIP_DL_TESTS = input('Run download tests (y/n)?: ').lower() != 'y'


class BasePlatformTests(unittest.TestCase):

    """Class providing base tests for all supported P2P platforms."""

    @unittest.skip('Skip tests for BasePlatformTests!')
    def setUp(self) -> None:
        """Dummy setUp, needs to be overridden by child classes."""
        self.name = None
        self.header = 0
        self.Platform = None
        self.unknown_cf_types = ''
        self.DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
        self.DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    @unittest.skipIf(SKIP_DL_TESTS, 'Skipping download tests!')
    def run_download_test(
            self, result_file: str, date_range: Tuple[date, date]) -> None:
        """
        Download platform account statement and compare it to result_file.

        Args:
            result_file: File with expected results without prefix or suffix.
            date_range: Date range for which to generate the account statement.

        """
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
                platform.statement, expected_results, header=self.header))

    def run_parser_test(
            self, result_file: str, date_range: Tuple[date, date],
            exp_unknown_cf_types: str = '') -> None:
        """
        Test the parser of the given platform.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            result_file: File with expected results without prefix or suffix.
            date_range: Date range tuple (start_date, end_date) for which the
                account statement was generated.
            exp_unknown_cf_types: Expected results for the unknown cashflow
                types.

        """
        exp_result_file = RESULT_PREFIX + result_file + '.csv'
        statement_without_suffix = INPUT_PREFIX + result_file

        platform = self.Platform(date_range, statement_without_suffix)
        (df, unknown_cf_types) = platform.parse_statement()

        df_exp = _get_expected_df(exp_result_file)

        # Round data frame to avoid minor rounding errors during the comparison
        df = df.round(2)

        # Reset the index to allow comparing index values/types too
        df.reset_index(inplace=True)

        # If df is empty, df.equals() will not work since we imported df_exp
        # with non-empty index_cols
        try:
            if df.empty:
                self.assertTrue(df_exp.empty)
            else:
                self.assertTrue(df.equals(df_exp))
        except AssertionError as err:
            print('df:', df, df.dtypes)
            print('df_exp:', df_exp, df_exp.dtypes)
            raise AssertionError(err)

        self.assertEqual(unknown_cf_types, exp_unknown_cf_types)

    def test_download_statement(self) -> None:
        """Test downloading account statement for default date_range."""
        self.run_download_test(
            'download_{}_statement'.format(self.name.lower()), self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        """
        Test downloading account statement for date_range without cashflows.
        """
        self.run_download_test(
            'download_{}_statement_no_cfs'.format(self.name.lower()),
            self.DATE_RANGE_NO_CFS)

    def test_parse_statement(self):
        """Test parsing platform default statement."""
        self.run_parser_test(
            '{}_parser'.format(self.name.lower()), self.DATE_RANGE)

    def test_parse_statement_no_cfs(self):
        """Test platform parser if there were no cashflows in date_range."""
        self.run_parser_test(
            '{}_parser_no_cfs'.format(self.name.lower()),
            self.DATE_RANGE_NO_CFS)

    def test_parse_statement_unknown_cf(self) -> None:
        """Test platform parser when unknown cashflow types are present."""
        if self.unknown_cf_types == '':
            self.skipTest('No unknown cashflow types for this platform!')
        self.run_parser_test(
            '{}_parser_unknown_cf'.format(self.name.lower()), self.DATE_RANGE,
            exp_unknown_cf_types=self.unknown_cf_types)


class BondoraTests(BasePlatformTests):

    """Class containing all tests for Bondora."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Bondora'
        self.Platform = p2p_platforms.Bondora
        self.unknown_cf_types = ''


class DoFinanceTests(BasePlatformTests):

    """Class containing all tests for DoFinance."""

    DATE_RANGE = (date(2018, 5, 1), date(2018, 8, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'DoFinance'
        self.Platform = p2p_platforms.DoFinance
        self.unknown_cf_types = \
            'Anlage\nRate: 6% Typ: automatisch, TestCF1, TestCF2'


class EstateguruTests(BasePlatformTests):

    """Class containing all tests for Estateguru."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Estateguru'
        self.Platform = p2p_platforms.Estateguru
        self.unknown_cf_types = \
            'Investition(AutoInvestieren), TestCF1, TestCF2'


class GrupeerTests(BasePlatformTests):

    """Class containing all tests for Grupeer."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Grupeer'
        self.Platform = p2p_platforms.Grupeer
        self.unknown_cf_types = 'TestCF1, TestCF2'


class IuvoTests(BasePlatformTests):

    """Class containing all tests for Iuvo."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Iuvo'
        self.Platform = p2p_platforms.Iuvo
        self.unknown_cf_types = 'TestCF1, TestCF2'


class MintosTests(BasePlatformTests):

    """Class containing all tests for Mintos."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Mintos'
        self.Platform = p2p_platforms.Mintos
        self.unknown_cf_types = 'Interestincome, TestCF1, TestCF2'


class PeerBerryTests(BasePlatformTests):

    """Class containing all tests for PeerBerry."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'PeerBerry'
        self.Platform = p2p_platforms.PeerBerry
        self.unknown_cf_types = ''


class RobocashTests(BasePlatformTests):

    """Class containing all tests for Robocash."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Robocash'
        self.Platform = p2p_platforms.Robocash
        self.unknown_cf_types = 'TestCF1, TestCF2'


class SwaperTests(BasePlatformTests):

    """Class containing all tests for Swaper."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Swaper'
        self.Platform = p2p_platforms.Swaper
        self.unknown_cf_types = ''


class TwinoTests(BasePlatformTests):

    """Class containing all tests for Twino."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))

    def setUp(self) -> None:
        self.name = 'Twino'
        self.header = 2
        self.Platform = p2p_platforms.Twino
        self.unknown_cf_types = 'TestCF1 PRINCIPAL, TestCF2 INTEREST'


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


def _get_expected_df(exp_result_file: str) -> pd.DataFrame:
    """
    Helper method to get the expected dataframe from the result file.

    Args:
        exp_result_file: File name including path which contains the
            dataframe with the expected test results.

    Returns:
        Dataframe with the expected test results.

    """
    df_exp = pd.read_csv(exp_result_file, index_col=[0, 1, 2])

    # Round data frame to avoid minor rounding errors during the comparison
    df_exp = df_exp.round(2)

    # Reset the index to allow comparing index values/types too
    df_exp.reset_index(inplace=True)
    df_exp.fillna('NaN', inplace=True)

    # Explicitly set the date column to datetime format
    df_exp['Datum'] = pd.to_datetime(df_exp['Datum'])

    return df_exp


if __name__ == '__main__':
    unittest.main()
