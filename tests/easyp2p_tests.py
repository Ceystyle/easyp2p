# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all parser tests for easyp2p."""

from datetime import date
import os
import sys
from typing import Sequence, Tuple
import unittest

import pandas as pd

from .context import (
    p2p_helper, p2p_parser, bondora, dofinance, estateguru, grupeer, iuvo,
    mintos, peerberry, robocash, swaper, twino)

PLATFORMS = {
    'Bondora': 'csv',
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
RESULT_PREFIX = os.path.join('tests', 'results', 'result_test_')


class P2PParserTests(unittest.TestCase):

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

        Keyword Args:
            date_range: Date range for which the account statement was
                generated
            unknown_cf_types_exp: Expected results for the unknown cashflow
                types

        """
        class_ = getattr(getattr(
            sys.modules[__name__], platform.lower()), platform)
        platform_instance = class_(date_range)
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
            print('df_exp:', df_exp,  df_exp.dtypes)
            raise AssertionError

        try:
            self.assertEqual(unknown_cf_types, unknown_cf_types_exp)
        except AssertionError:
            print('unknown_cf_types:',  unknown_cf_types)
            print('unknown_cf_types_exp:')
            raise AssertionError

    def test_parser(self):
        """Test parsing default statements."""
        for platform in PLATFORMS.keys():
            test_name = '{0}_parser'.format(platform.lower())
            if platform == 'DoFinance':
                self.run_parser_test(
                    platform, (INPUT_PREFIX + test_name + '.'
                    + PLATFORMS[platform]), RESULT_PREFIX + test_name + '.csv',
                    date_range=(date(2018, 5, 1), date(2018, 9, 30)))
            else:
                self.run_parser_test(
                    platform, (INPUT_PREFIX + test_name + '.'
                    + PLATFORMS[platform]), RESULT_PREFIX + test_name + '.csv')

    def test_parser_missing_month(self):
        """Test parsing statements if a month in date_range is missing."""
        for platform in PLATFORMS.keys():
            test_name = '{0}_parser_missing_month'.format(platform.lower())
            if platform == 'DoFinance':
                self.run_parser_test(
                    platform, (INPUT_PREFIX + test_name + '.'
                    + PLATFORMS[platform]), RESULT_PREFIX + test_name + '.csv',
                    date_range=(date(2018, 5, 1), date(2018, 9, 30)))
            else:
                self.run_parser_test(
                    platform, (INPUT_PREFIX + test_name + '.'
                    + PLATFORMS[platform]), RESULT_PREFIX + test_name + '.csv',
                    self.date_range_missing_month)

    def test_parser_no_cfs(self):
        """Test parsing statements if there were no cashflows in date_range."""
        for platform in PLATFORMS.keys():
            test_name = '{0}_parser_no_cfs'.format(platform.lower())
            self.run_parser_test(
                platform, (INPUT_PREFIX + test_name + '.'
                + PLATFORMS[platform]), RESULT_PREFIX + test_name + '.csv',
                self.date_range_no_cfs)

    def test_dofinance_parser_unknown_cf(self):
        """
        Test parsing DoFinance statement if unknown cashflow types are present.
        """
        test_name = 'dofinance_parser_unknown_cf'
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        self.run_parser_test(
            'dofinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', dofinance_date_range,
            unknown_cf_types_exp=
            'Anlage\nRate: 6% Typ: automatisch, TestCF1, TestCF2')

    def test_dofinance_parser_wrong_column_names(self):
        """Test DoFinance parser if there are unknown column names."""
        self.assertRaises(
            RuntimeError, dofinance.parse_statement,
            (date(2018, 9, 1), date(2018, 12, 31)),
            INPUT_PREFIX + 'dofinance_parser_wrong_column_names.xlsx')

    def test_estateguru_parser_unknown_cf(self):
        """Test Estateguru parser if unknown cashflow types are present."""
        test_name = 'estateguru_parser_unknown_cf.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            unknown_cf_types_exp=
            'Investition(AutoInvestieren), TestCF1, TestCF2')

    def test_grupeer_parser_unknown_cf(self):
        """
        Test parsing Grupeer statement if unknown cashflow types are present.
        """
        test_name = 'grupeer_parser_unknown_cf'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_grupeer_parser_unknown_currency(self):
        """Test Grupeer parser if unknown currencies types are present."""
        test_name = 'grupeer_parser_unknown_currency'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_iuvo_parser_unknown_cf(self):
        """
        Test parsing Iuvo statement if unknown cashflow types are present.
        """
        test_name = 'iuvo_parser_unknown_cf'
        self.run_parser_test(
            'iuvo', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_mintos_parser_unknown_cf(self):
        """
        Test parsing Mintos statement if unknown cashflow types are present.
        """
        test_name = 'mintos_parser_unknown_cf'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='Interestincome, TestCF1, TestCF2')

    def test_peerberry_parser_no_cfs(self):
        """Test Peerberry parser if there were no cashflows in date_range."""
        test_name = 'peerberry_parser_no_cfs'
        self.run_parser_test(
            'peerberry', INPUT_PREFIX + test_name + '.csv',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_robocash_parser_unknown_cf(self):
        """
        Test parsing Robocash statement if unknown cashflow types are present.
        """
        test_name = 'robocash_parser_unknown_cf'
        self.run_parser_test(
            'robocash', INPUT_PREFIX + test_name + '.xls',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp=('TestCF1, TestCF2'))

    def test_twino_parser_unknown_cf(self):
        """
        Test parsing Twino statement if unknown cashflow types are present.
        """
        test_name = 'twino_parser_unknown_cf'
        self.run_parser_test(
            'twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp=('TestCF1 PRINCIPAL, TestCF2 INTEREST'))

    def test_twino_parser_wrong_column_names(self):
        """
        Test Twino parser if unknown column names are present in the statement.
        """
        self.assertRaises(
            RuntimeError, twino.parse_statement,
            (date(2018, 9, 1), date(2018, 12, 31)),
            INPUT_PREFIX + 'twino_parser_wrong_column_names.xlsx')

    def run_show_results(
            self, list_of_dfs: Sequence[pd.DataFrame], result_file: str,
            exp_result_file: str) -> None:
        """
        Test the show_results functionality for the given platforms.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            list_of_dfs: List with the parsed account statements
            result_file: output file of show_results
            exp_result_file: file with expected results

        """
        p2p_parser.show_results(
            list_of_dfs, result_file)

        month_pivot_table = pd.read_excel(
            result_file, 'Monatsergebnisse')
        month_pivot_table_exp = pd.read_excel(
            exp_result_file, 'Monatsergebnisse')
        totals_pivot_table = pd.read_excel(
            result_file, 'Gesamtergebnis')
        totals_pivot_table_exp = pd.read_excel(
            exp_result_file, 'Gesamtergebnis')

        self.assertTrue(month_pivot_table.equals(month_pivot_table_exp))
        self.assertTrue(totals_pivot_table.equals(totals_pivot_table_exp))

    def test_show_results_all(self):
        """Test show_results for all supported platforms."""
        list_of_dfs = []

        for platform in PLATFORMS:
            df = p2p_helper.get_df_from_file(
                RESULT_PREFIX + '{0}_parser.csv'.format(
                    platform.lower()))
            df.set_index(['Plattform', 'Datum', 'Währung'], inplace=True)
            list_of_dfs.append(df)

        self.run_show_results(
            list_of_dfs, 'test_show_results_all.xlsx',
            RESULT_PREFIX + 'show_results_all.xlsx')

    def test_show_results_estateguru(self):
        """Test show_results for Estateguru."""

        df = p2p_helper.get_df_from_file(
            RESULT_PREFIX + 'estateguru_parser.csv')
        df.set_index(['Plattform', 'Datum', 'Währung'], inplace=True)

        self.run_show_results(
            [df], 'test_show_results_estateguru.xlsx',
            RESULT_PREFIX + 'show_results_estateguru.xlsx')


def are_files_equal(
        file1: str, file2: str,
        drop_header: bool = False) -> bool:
    """
    Function to determine if two files are equal.

    Args:
        file1 (str): Name including path of first file
        file2 (str): Name including path of second file

    Keyword Args:
        drop_header: If True the header of the files will be ignored in the
            comparison

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
    unittest.main()
