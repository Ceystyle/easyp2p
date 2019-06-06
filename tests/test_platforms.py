# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module with statement download tests for all supported P2P platforms."""

from datetime import date
import os
import tempfile
from typing import Sequence, Tuple
import unittest

import pandas as pd

from easyp2p.excel_writer import (
    write_results, DAILY_RESULTS, MONTHLY_RESULTS, TOTAL_RESULTS)
from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import get_df_from_file, P2PParser
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
        self.unknown_cf_types = []
        self.DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
        self.DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
        self.DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

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
            input_file: str = None,
            exp_unknown_cf_types: Sequence[str] = []) -> None:
        """
        Test the parser of the given platform.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            result_file: File with expected results without prefix or suffix.
            date_range: Date range tuple (start_date, end_date) for which the
                account statement was generated.
            input_file: Location of the input statement for the parser without
                suffix. If None INPUT_PREFIX + result_file will be used by
                default.
            exp_unknown_cf_types: Expected results for the unknown cash flow
                types.

        """
        exp_result_file = RESULT_PREFIX + result_file + '.csv'
        if input_file is None:
            statement_without_suffix = INPUT_PREFIX + result_file
        else:
            statement_without_suffix = input_file

        platform = self.Platform(date_range, statement_without_suffix)
        (df, unknown_cf_types) = platform.parse_statement()
        # df.to_csv('tests/test_results/test_' + result_file + '.csv')
        df.to_csv('tests/test_results/test_multicurrency.csv')

        df_exp = _get_expected_df(exp_result_file)

        # Round data frame to avoid minor rounding errors during the comparison
        df = df.round(5)

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
            show_diffs(df, df_exp)
            raise AssertionError(err)

        self.assertEqual(unknown_cf_types, exp_unknown_cf_types)

    def run_write_results(
            self, input_file: str, exp_result_file: str,
            date_range: Tuple[date, date]) -> None:
        """
        Test the write_results functionality for the given platforms.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            input_file: Input file which contains the parsed results of all
                selected P2P platforms.
            exp_result_file: File with expected results.
            date_range: Date range for which to generate the results file.

        """
        df = get_df_from_file(input_file)
        df.set_index([
            P2PParser.PLATFORM, P2PParser.DATE, P2PParser.CURRENCY],
            inplace=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            #output_file = os.path.join(temp_dir, 'test_write_results.xlsx')
            output_file = 'tests/test_results/test_write_results.xlsx'
            write_results(df, output_file, date_range)

            for worksheet in [DAILY_RESULTS, MONTHLY_RESULTS, TOTAL_RESULTS]:
                df = pd.read_excel(output_file, worksheet, index_col=[0, 1, 2])
                df_exp = pd.read_excel(
                    exp_result_file, worksheet, index_col=[0, 1, 2])
                try:
                    self.assertTrue(df.equals(df_exp))
                except AssertionError:
                    show_diffs(df, df_exp)
                    raise AssertionError

    def test_download_statement(self) -> None:
        """Test downloading account statement for default date_range."""
        self.run_download_test(
            'download_{}_statement'.format(self.name.lower()), self.DATE_RANGE)

    def test_download_statement_no_cfs(self) -> None:
        """
        Test downloading account statement for date_range without cash flows.
        """
        self.run_download_test(
            'download_{}_statement_no_cfs'.format(self.name.lower()),
            self.DATE_RANGE_NO_CFS)

    def test_parse_statement(self):
        """Test parsing platform default statement."""
        self.run_parser_test(
            '{}_parser'.format(self.name.lower()), self.DATE_RANGE,
            RESULT_PREFIX+'download_{}_statement'.format(self.name.lower()))

    def test_parse_statement_no_cfs(self):
        """Test platform parser if there were no cash flows in date_range."""
        self.run_parser_test(
            '{}_parser_no_cfs'.format(self.name.lower()),
            self.DATE_RANGE_NO_CFS,
            input_file=RESULT_PREFIX+'download_{}_statement_no_cfs'.format(
                self.name.lower()))

    def test_parse_statement_unknown_cf(self) -> None:
        """Test platform parser when unknown cash flow types are present."""
        if self.unknown_cf_types == []:
            self.skipTest('No unknown cash flow types for this platform!')
        self.run_parser_test(
            '{}_parser_unknown_cf'.format(self.name.lower()), self.DATE_RANGE,
            exp_unknown_cf_types=self.unknown_cf_types)

    def test_parse_statement_missing_month(self):
        self.run_parser_test(
            '{}_parser_missing_month'.format(self.name.lower()),
            self.DATE_RANGE_MISSING_MONTH)

    def test_write_results(self):
        """Test write_results when cash flows are present for all months."""
        self.run_write_results(
            RESULT_PREFIX + '{}_parser.csv'.format(self.name.lower()),
            RESULT_PREFIX + 'write_results_{}.xlsx'.format(self.name.lower()),
            self.DATE_RANGE)

    def test_write_results_no_cfs(self):
        """Test write_results when there were no cash flows in date range."""
        self.run_write_results(
            RESULT_PREFIX + '{}_parser_no_cfs.csv'.format(self.name.lower()),
            RESULT_PREFIX + 'write_results_{}_no_cfs.xlsx'.format(
                self.name.lower()),
            self.DATE_RANGE_NO_CFS)

    def test_write_results_missing_month(self):
        """
        Test write_results when there are months without cash flows.
        """
        self.run_write_results(
            RESULT_PREFIX + '{}_parser_missing_month.csv'.format(
                self.name.lower()),
            RESULT_PREFIX + 'write_results_{}_missing_month.xlsx'.format(
                self.name.lower()),
            self.DATE_RANGE_MISSING_MONTH)


class BondoraTests(BasePlatformTests):

    """Class containing all tests for Bondora."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Bondora'
        self.Platform = p2p_platforms.Bondora
        self.unknown_cf_types = []
        self.header = 0

    # Below are some tests for write_results which affect more than just one
    # platform.
    def test_write_results_mixed_no_cfs(self):
        """
        Test write_results with one platform with and one without cash flows.
        """
        self.run_write_results(
            INPUT_PREFIX + 'write_results_mixed_no_cfs.csv',
            RESULT_PREFIX + 'write_results_mixed_no_cfs.xlsx',
            self.DATE_RANGE)

    def test_write_results_all(self):
        """Test write_results for all supported platforms."""
        self.run_write_results(
            INPUT_PREFIX + 'write_results_all.csv',
            RESULT_PREFIX + 'write_results_all.xlsx', self.DATE_RANGE)

    def test_write_results_all_missing_month(self):
        """Test write_results for all supported platforms."""
        self.run_write_results(
            INPUT_PREFIX + 'write_results_all_missing_month.csv',
            RESULT_PREFIX + 'write_results_all_missing_month.xlsx',
            self.DATE_RANGE_MISSING_MONTH)


class DoFinanceTests(BasePlatformTests):

    """Class containing all tests for DoFinance."""

    DATE_RANGE = (date(2018, 1, 1), date(2018, 8, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 4, 1), date(2018, 9, 30))

    def setUp(self) -> None:
        self.name = 'DoFinance'
        self.Platform = p2p_platforms.DoFinance
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 0


class EstateguruTests(BasePlatformTests):

    """Class containing all tests for Estateguru."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Estateguru'
        self.Platform = p2p_platforms.Estateguru
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 0


class GrupeerTests(BasePlatformTests):

    """Class containing all tests for Grupeer."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Grupeer'
        self.Platform = p2p_platforms.Grupeer
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 0


class IuvoTests(BasePlatformTests):

    """Class containing all tests for Iuvo."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Iuvo'
        self.Platform = p2p_platforms.Iuvo
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 3


class MintosTests(BasePlatformTests):

    """Class containing all tests for Mintos."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Mintos'
        self.Platform = p2p_platforms.Mintos
        self.unknown_cf_types = ['Interestincome', 'TestCF1', 'TestCF2']
        self.header = 0

    def test_parser_multicurrency(self) -> None:
        """Test parser if more than one currency is present."""
        self.run_parser_test(
            'mintos_parser_multicurrency',
            self.DATE_RANGE, INPUT_PREFIX + 'mintos_parser_multicurrency')

    def test_write_results_multicurrency(self) -> None:
        """Test write_results if more than one currency is present."""
        self.run_write_results(
            INPUT_PREFIX + 'write_results_multicurrency.csv',
            RESULT_PREFIX + 'write_results_multicurrency.xlsx',
            self.DATE_RANGE)


class PeerBerryTests(BasePlatformTests):

    """Class containing all tests for PeerBerry."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'PeerBerry'
        self.Platform = p2p_platforms.PeerBerry
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 0


class RobocashTests(BasePlatformTests):

    """Class containing all tests for Robocash."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Robocash'
        self.Platform = p2p_platforms.Robocash
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 0


class SwaperTests(BasePlatformTests):

    """Class containing all tests for Swaper."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Swaper'
        self.Platform = p2p_platforms.Swaper
        self.unknown_cf_types = ['TestCF1', 'TestCF2']
        self.header = 0


class TwinoTests(BasePlatformTests):

    """Class containing all tests for Twino."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

    def setUp(self) -> None:
        self.name = 'Twino'
        self.Platform = p2p_platforms.Twino
        self.unknown_cf_types = ['TestCF1 PRINCIPAL', 'TestCF2 INTEREST']
        self.header = 2


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
    df_exp = df_exp.round(5)

    # Reset the index to allow comparing index values/types too
    df_exp.reset_index(inplace=True)
    df_exp.fillna('NaN', inplace=True)

    # Explicitly set the date column to datetime format
    df_exp[P2PParser.DATE] = pd.to_datetime(df_exp[P2PParser.DATE])

    return df_exp


def show_diffs(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """
    Prints differences between two DataFrames.

    Args:
        df1: DataFrame to compare.
        df2: Reference DataFrame for comparison.

    """
    try:
        df1.fillna('dummy', inplace=True)
        df2.fillna('dummy', inplace=True)
        df_diff = (df1 != df2)
        print(
            df1.loc[df_diff.any(1), df_diff.any(0)],
            df2.loc[df_diff.any(1), df_diff.any(0)])
    except ValueError:
        # Column names or row numbers do not match
        print(
            'Unexpected columns:',
            [column for column in df1.columns if column not in df2.columns])
        print(
            'Missing columns:',
            [column for column in df2.columns if column not in df1.columns])
        print(
            'Unexpected rows:',
            df1.loc[[index for index in df1.index if index not in df2.index]])
        print(
            'Missing rows:',
            df2.loc[[index for index in df2.index if index not in df1.index]])


if __name__ == '__main__':
    unittest.main()