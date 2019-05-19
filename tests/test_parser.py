# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all tests write_results in p2p_parser."""

import os
import tempfile
import unittest

import pandas as pd

from easyp2p.p2p_parser import get_df_from_file
import easyp2p.p2p_parser as p2p_parser
from easyp2p.p2p_parser import P2PParser
from tests import INPUT_PREFIX, RESULT_PREFIX


class WriteResultsTests(unittest.TestCase):

    """Contains all p2p_parser.write_results tests."""

    def run_write_results(self, input_file: str, exp_result_file: str) -> None:
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
            p2p_parser.write_results(df, output_file)

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

    def test_write_results_bondora(self):
        """Test write_results if only Bondora is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'bondora_parser.csv',
            RESULT_PREFIX + 'write_results_bondora.xlsx')

    def test_write_results_dofinance(self):
        """Test write_results if only DoFinance is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'dofinance_parser.csv',
            RESULT_PREFIX + 'write_results_dofinance.xlsx')

    def test_write_results_estateguru(self):
        """Test write_results if only Estateguru is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'estateguru_parser.csv',
            RESULT_PREFIX + 'write_results_estateguru.xlsx')

    def test_write_results_grupeer(self):
        """Test write_results if only Grupeer is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'grupeer_parser.csv',
            RESULT_PREFIX + 'write_results_grupeer.xlsx')

    def test_write_results_iuvo(self):
        """Test write_results if only Iuvo is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'iuvo_parser.csv',
            RESULT_PREFIX + 'write_results_iuvo.xlsx')

    def test_write_results_mintos(self):
        """Test write_results if only Mintos is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'mintos_parser.csv',
            RESULT_PREFIX + 'write_results_mintos.xlsx')

    def test_write_results_peerberry(self):
        """Test write_results if only PeerBerry is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'peerberry_parser.csv',
            RESULT_PREFIX + 'write_results_peerberry.xlsx')

    def test_write_results_robocash(self):
        """Test write_results if only Robocash is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'robocash_parser.csv',
            RESULT_PREFIX + 'write_results_robocash.xlsx')

    def test_write_results_swaper(self):
        """Test write_results if only Swaper is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'swaper_parser.csv',
            RESULT_PREFIX + 'write_results_swaper.xlsx')

    def test_write_results_twino(self):
        """Test write_results if only Twino is selected."""
        self.run_write_results(
            RESULT_PREFIX + 'twino_parser.csv',
            RESULT_PREFIX + 'write_results_twino.xlsx')

    def test_write_results_all(self):
        """Test write_results for all supported platforms."""
        self.run_write_results(
            INPUT_PREFIX + 'write_results_all.csv',
            RESULT_PREFIX + 'write_results_all.xlsx')


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
    unittest.main()
