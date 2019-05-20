# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all tests write_results in p2p_parser."""

from datetime import date
import os
import tempfile
import unittest
from typing import Tuple

import pandas as pd

from easyp2p.p2p_parser import get_df_from_file
import easyp2p.p2p_parser as p2p_parser
from easyp2p.p2p_parser import P2PParser
from tests import INPUT_PREFIX, RESULT_PREFIX


class WriteResultsTests(unittest.TestCase):

    """Contains all p2p_parser.write_results tests."""

    DATE_RANGE = (date(2018, 9, 1), date(2018, 12, 31))
    DATE_RANGE_NO_CFS = (date(2016, 9, 1), date(2016, 12, 31))
    DATE_RANGE_MISSING_MONTH = (date(2018, 8, 1), date(2019, 1, 31))

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

        """
        df = get_df_from_file(input_file)
        df.set_index([
            P2PParser.PLATFORM, P2PParser.DATE, P2PParser.CURRENCY],
            inplace=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, 'test_write_results.xlsx')
            p2p_parser.write_results(df, output_file, date_range)

            for worksheet in [
                    p2p_parser.DAILY_RESULTS, p2p_parser.MONTHLY_RESULTS,
                    p2p_parser.TOTAL_RESULTS]:
                df = pd.read_excel(output_file, worksheet, index_col=[0, 1, 2])
                df_exp = pd.read_excel(
                    exp_result_file, worksheet, index_col=[0, 1, 2])
                try:
                    self.assertTrue(df.equals(df_exp))
                except AssertionError:
                    show_diffs(df, df_exp)
                    raise AssertionError

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


if __name__ == "__main__":
    unittest.main()
