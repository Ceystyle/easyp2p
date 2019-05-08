# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all parser tests for easyp2p."""

from datetime import date
import os
from typing import Optional, Tuple
import unittest

import pandas as pd

import easyp2p.p2p_helper as p2p_helper
import easyp2p.p2p_parser as p2p_parser
import easyp2p.platforms as p2p_platforms

PLATFORMS = {
    'Bondora': 'xlsx',
    'DoFinance': 'xlsx',
    'Estateguru': 'csv',
    'Grupeer': 'xlsx',
    'Iuvo': 'xlsx',
    'Mintos': 'xlsx',
    'PeerBerry': 'csv',
    'Robocash': 'xls',
    'Swaper': 'xlsx',
    'Twino': 'xlsx'}
INPUT_PREFIX = os.path.join('tests', 'input', 'input_test_')
RESULT_PREFIX = os.path.join('tests', 'expected_results', 'result_test_')


class ParserTests(unittest.TestCase):

    """Contains all p2p_parser tests."""

    def setUp(self):
        """Initialize the default arguments for p2p_parser."""
        self.date_range = (date(2018, 9, 1), date(2018, 12, 31))
        self.date_range_missing_month = (date(2018, 8, 1), date(2018, 12, 31))
        self.date_range_no_cfs = (date(2016, 9, 1), date(2016, 12, 31))

    def run_parser_test(
            self, platform: str, input_file: str,
            exp_result_file: str,
            date_range: Tuple[date, date] =
                (date(2018, 9, 1), date(2018, 12, 31)),
            unknown_cf_types_exp: str = '') -> None:
        """
        Test the parser of the given platform.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            platform: Name of the P2P platform
            input_file: Input file name including path for the parser
            exp_result_file: File name including path with expected results
            date_range: Date range tuple (start_date, end_date) for which the
                account statement was generated
            unknown_cf_types_exp: Expected results for the unknown cashflow
                types

        """
        platform_class = getattr(p2p_platforms, platform)
        platform_instance = platform_class(date_range)
        (df, unknown_cf_types) = platform_instance.parse_statement(
            input_file)
        df_exp = pd.read_csv(
            exp_result_file, index_col=[0, 1, 2])

        # Round both data frames to two digits to avoid minor rounding errors
        # during the comparison
        df = df.round(2)
        df_exp = df_exp.round(2)

        # Reset the index to allow comparing index values/types too
        df.reset_index(inplace=True)
        df_exp.reset_index(inplace=True)
        df_exp.fillna('NaN', inplace=True)

        # Explicitly set the date column to datetime format
        df_exp['Datum'] = pd.to_datetime(df_exp['Datum'])

        # If df is empty, df.equals() will not work since we imported df_exp
        # with non-empty index_cols
        try:
            if df.empty:
                self.assertTrue(df_exp.empty)
            else:
                self.assertTrue(df.equals(df_exp))
        except AssertionError:
            print('df:', df, df.dtypes)
            print('df_exp:', df_exp, df_exp.dtypes)
            raise AssertionError

        try:
            self.assertEqual(unknown_cf_types, unknown_cf_types_exp)
        except AssertionError:
            print('unknown_cf_types:', unknown_cf_types)
            print('unknown_cf_types_exp:')
            raise AssertionError

    def default_parser_test(
            self, platform: str,
            date_range: Optional[Tuple[date, date]] = None) -> None:
        """Test parsing default statements."""
        test_name = '{0}_parser'.format(platform.lower())
        if date_range is None:
            date_range = self.date_range

        self.run_parser_test(
            platform,
            INPUT_PREFIX + test_name + '.' + PLATFORMS[platform],
            RESULT_PREFIX + test_name + '.csv', date_range=date_range)

    def no_cfs_parser_test(
            self, platform: str,
            date_range: Optional[Tuple[date, date]] = None) -> None:
        """Test parsing statements if there were no cashflows in date_range."""
        test_name = '{0}_parser_no_cfs'.format(platform.lower())
        if date_range is None:
            date_range = self.date_range_no_cfs

        self.run_parser_test(
            platform,
            INPUT_PREFIX + test_name + '.' + PLATFORMS[platform],
            RESULT_PREFIX + test_name + '.csv', date_range=date_range)

    def test_bondora_parser(self):
        """Test parsing Bondora default statement."""
        self.default_parser_test('Bondora')

    def test_bondora_parser_no_cfs(self):
        """Test Bondora parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Bondora')

    def test_dofinance_parser(self):
        """Test parsing DoFinance default statement."""
        self.default_parser_test(
            'DoFinance', date_range=(date(2018, 5, 1), date(2018, 9, 30)))

    def test_dofinance_parser_no_cfs(self):
        """Test DoFinance parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('DoFinance')

    def test_dofinance_parser_unknown_cf(self):
        """
        Test parsing DoFinance statement if unknown cashflow types are present.
        """
        test_name = 'dofinance_parser_unknown_cf'
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        self.run_parser_test(
            'DoFinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', dofinance_date_range,
            unknown_cf_types_exp=
            'Anlage\nRate: 6% Typ: automatisch, TestCF1, TestCF2')

    def test_dofinance_parser_wrong_column_names(self):
        """Test DoFinance parser if there are unknown column names."""
        dofinance = p2p_platforms.dofinance.DoFinance(
            (date(2018, 5, 1), date(2018, 9, 30)))
        self.assertRaises(
            RuntimeError, dofinance.parse_statement,
            INPUT_PREFIX + 'dofinance_parser_wrong_column_names.xlsx')

    def test_estateguru_parser(self):
        """Test parsing Estateguru default statement."""
        self.default_parser_test('Estateguru')

    def test_estateguru_parser_no_cfs(self):
        """Test Estateguru parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Estateguru')

    def test_estateguru_parser_unknown_cf(self):
        """Test Estateguru parser if unknown cashflow types are present."""
        test_name = 'estateguru_parser_unknown_cf.csv'
        self.run_parser_test(
            'Estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            unknown_cf_types_exp=
            'Investition(AutoInvestieren), TestCF1, TestCF2')

    def test_grupeer_parser(self):
        """Test parsing Grupeer default statement."""
        self.default_parser_test('Grupeer')

    def test_grupeer_parser_no_cfs(self):
        """Test Grupeer parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Grupeer')

    def test_grupeer_parser_unknown_cf(self):
        """
        Test parsing Grupeer statement if unknown cashflow types are present.
        """
        test_name = 'grupeer_parser_unknown_cf'
        self.run_parser_test(
            'Grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_iuvo_parser(self):
        """Test parsing Iuvo default statement."""
        self.default_parser_test('Iuvo')

    def test_iuvo_parser_no_cfs(self):
        """Test Iuvo parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Iuvo')

    def test_iuvo_parser_unknown_cf(self):
        """
        Test parsing Iuvo statement if unknown cashflow types are present.
        """
        test_name = 'iuvo_parser_unknown_cf'
        self.run_parser_test(
            'Iuvo', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_mintos_parser(self):
        """Test parsing Mintos default statement."""
        self.default_parser_test('Mintos')

    def test_mintos_parser_no_cfs(self):
        """Test Mintos parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Mintos')

    def test_mintos_parser_unknown_cf(self):
        """
        Test parsing Mintos statement if unknown cashflow types are present.
        """
        test_name = 'mintos_parser_unknown_cf'
        self.run_parser_test(
            'Mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='Interestincome, TestCF1, TestCF2')

    def test_peerberry_parser(self):
        """Test parsing PeerBerry default statement."""
        self.default_parser_test('PeerBerry')

    def test_peerberry_parser_no_cfs(self):
        """Test PeerBerry parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('PeerBerry')

    def test_robocash_parser(self):
        """Test parsing Robocash default statement."""
        self.default_parser_test('Robocash')

    def test_robocash_parser_no_cfs(self):
        """Test Robocash parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Robocash')

    def test_robocash_parser_unknown_cf(self):
        """
        Test parsing Robocash statement if unknown cashflow types are present.
        """
        test_name = 'robocash_parser_unknown_cf'
        self.run_parser_test(
            'Robocash', INPUT_PREFIX + test_name + '.xls',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_swaper_parser(self):
        """Test parsing Swaper default statement."""
        self.default_parser_test('Swaper')

    def test_swaper_parser_no_cfs(self):
        """Test Swaper parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Swaper')

    def test_twino_parser(self):
        """Test parsing Twino default statement."""
        self.default_parser_test('Twino')

    def test_twino_parser_no_cfs(self):
        """Test Twino parser if there were no cashflows in date_range."""
        self.no_cfs_parser_test('Twino')

    def test_twino_parser_unknown_cf(self):
        """
        Test parsing Twino statement if unknown cashflow types are present.
        """
        test_name = 'twino_parser_unknown_cf'
        self.run_parser_test(
            'Twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1 PRINCIPAL, TestCF2 INTEREST')

    def test_twino_parser_wrong_column_names(self):
        """
        Test Twino parser if unknown column names are present in the statement.
        """
        twino = p2p_platforms.twino.Twino(
            (date(2018, 9, 1), date(2018, 12, 31)))
        self.assertRaises(
            RuntimeError, twino.parse_statement,
            INPUT_PREFIX + 'twino_parser_wrong_column_names.xlsx')

    def run_write_results(
            self, df_result: pd.DataFrame, result_file: str,
            exp_result_file: str) -> None:
        """
        Test the write_results functionality for the given platforms.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            df_result: DataFrame containing the parsed results
            result_file: Output file of write_results
            exp_result_file: File with expected results

        """
        p2p_parser.write_results(df_result, result_file)

        daily_pivot_table = pd.read_excel(
            result_file, 'Tagesergebnisse')
        daily_pivot_table_exp = pd.read_excel(
            exp_result_file, 'Tagesergebnisse')
        monthly_pivot_table = pd.read_excel(
            result_file, 'Monatsergebnisse')
        monthly_pivot_table_exp = pd.read_excel(
            exp_result_file, 'Monatsergebnisse')
        totals_pivot_table = pd.read_excel(
            result_file, 'Gesamtergebnis')
        totals_pivot_table_exp = pd.read_excel(
            exp_result_file, 'Gesamtergebnis')

        try:
            self.assertTrue(daily_pivot_table.equals(daily_pivot_table_exp))
        except AssertionError:
            print('Actual result:\n', daily_pivot_table)
            print('Expected result:\n', daily_pivot_table_exp)
            raise AssertionError

        try:
            self.assertTrue(monthly_pivot_table.equals(monthly_pivot_table_exp))
        except AssertionError:
            print('Actual result:\n', monthly_pivot_table)
            print('Expected result:\n', monthly_pivot_table_exp)
            raise AssertionError

        try:
            self.assertTrue(totals_pivot_table.equals(totals_pivot_table_exp))
        except AssertionError:
            print('Actual result:\n', totals_pivot_table)
            print('Expected result:\n', totals_pivot_table_exp)
            raise AssertionError

    def test_write_results_all(self):
        """Test write_results for all supported platforms."""
        df_result = pd.DataFrame()

        for platform in PLATFORMS:
            df = p2p_helper.get_df_from_file(
                RESULT_PREFIX + '{0}_parser.csv'.format(
                    platform.lower()))
            df.set_index(['Plattform', 'Datum', 'Währung'], inplace=True)
            df_result = df_result.append(df, sort=True)

        self.run_write_results(
            df_result, 'test_write_results_all.xlsx',
            RESULT_PREFIX + 'write_results_all.xlsx')


def are_files_equal(
        file1: str, file2: str,
        drop_header: bool = False) -> bool:
    """
    Function to determine if two files are equal.

    Args:
        file1: Name including path of first file
        file2: Name including path of second file
        drop_header: If True the header of the files will be ignored in the
            comparison. Default is False.

    Returns:
        bool: True if the files are equal, False if not or if at least one
        of the files does not exist

    """
    try:
        df1 = p2p_helper.get_df_from_file(file1)
        df2 = p2p_helper.get_df_from_file(file2)
    except RuntimeError:
        return False

    if drop_header:
        df1 = drop_df_header(df1)
        df2 = drop_df_header(df2)

    return df1.equals(df2)


def drop_df_header(df: pd.DataFrame) -> pd.DataFrame:
    """
    Helper function to drop the header of a pandas DataFrame.

    Args:
        df: DataFrame including header

    Returns:
        DataFrame with the header row removed.

    """
    df = df[1:]   # The first row only contains a generic header
    new_header = df.iloc[0]  # Get the new first row as header
    df = df[1:]  # Remove the first row
    df.columns = new_header  # Set the new header

    return df


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(ParserTests)
    result = runner.run(suite)
