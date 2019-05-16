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


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(ParserTests)
    result = runner.run(suite)
