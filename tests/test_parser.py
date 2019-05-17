# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all tests write_results in p2p_parser."""

import os
import unittest

import pandas as pd

from easyp2p.p2p_parser import get_df_from_file
import easyp2p.p2p_parser as p2p_parser
from tests import RESULT_PREFIX, PLATFORMS


class ParserTests(unittest.TestCase):

    """Contains all p2p_parser.write_results tests."""

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

        df_daily = pd.read_excel(
            result_file, 'Tagesergebnisse', parse_dates=[2])
        exp_df_daily = pd.read_excel(
            exp_result_file, 'Tagesergebnisse', parse_dates=[2])
        df_monthly = pd.read_excel(
            result_file, 'Monatsergebnisse')
        exp_df_monthly = pd.read_excel(
            exp_result_file, 'Monatsergebnisse')
        df_total = pd.read_excel(
            result_file, 'Gesamtergebnis')
        exp_df_total = pd.read_excel(
            exp_result_file, 'Gesamtergebnis')

        try:
            self.assertTrue(df_daily.equals(exp_df_daily))
        except AssertionError:
            show_diffs(df_daily, exp_df_daily)
            raise AssertionError

        try:
            self.assertTrue(df_monthly.equals(exp_df_monthly))
        except AssertionError:
            show_diffs(df_monthly, exp_df_monthly)
            raise AssertionError

        try:
            self.assertTrue(df_total.equals(exp_df_total))
        except AssertionError:
            show_diffs(df_total, exp_df_total)
            raise AssertionError

    def test_write_results_all(self):
        """Test write_results for all supported platforms."""
        df_result = pd.DataFrame()

        for platform in PLATFORMS:
            df = get_df_from_file(RESULT_PREFIX + '{0}_parser.csv'.format(
                platform.lower()))
            df.set_index(['Plattform', 'Datum', 'Währung'], inplace=True)
            df_result = df_result.append(df, sort=True)

        result_file = os.path.join('tests', 'test_write_results_all.xlsx')
        self.run_write_results(
            df_result, result_file, RESULT_PREFIX + 'write_results_all.xlsx')

        # Clean up after test
        if os.path.isfile(result_file):
            os.remove(result_file)


def show_diffs(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """
    Prints differences between two DataFrames.

    Args:
        df1: First DataFrame to compare.
        df2: Second DataFrame to compare.

    """
    try:
        df_diff = (df1 != df2)
        print(df1.loc[df_diff.any(1), df_diff.any(0)])
        print(df2.loc[df_diff.any(1), df_diff.any(0)])
    except ValueError:
        # Column names do not match
        print(
            'Unexpected columns:',
            [column for column in df1.columns if column not in df2.columns])
        print(
            'Missing columns:',
            [column for column in df2.columns if column not in df1.columns])


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(ParserTests)
    result = runner.run(suite)
