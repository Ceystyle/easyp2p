# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module containing all tests for p2p_worker."""

from datetime import date
import os
import unittest
from unittest.mock import patch

import pandas as pd

from easyp2p.p2p_settings import Settings
from easyp2p.p2p_signals import PlatformFailedError
from easyp2p.p2p_worker import WorkerThread
import easyp2p.platforms


class WorkerTests(unittest.TestCase):

    """Contains all p2p_worker tests."""

    def setUp(self) -> None:
        """Initialize the WorkerThread."""
        self.settings = Settings(
            (date(2018, 9, 1), date(2018, 12, 31)),
            os.path.join(os.getcwd(), 'test.xlsx'))
        self.settings.platforms = {
            pl for pl in dir(easyp2p.platforms) if pl[0].isupper()}
        self.worker = WorkerThread(self.settings)
        self.worker.signals.abort = False

    def test_get_platform_instance(self):
        """Test get_platform_instance for all supported platforms."""
        for platform in self.settings.platforms:
            platform_instance = self.worker.get_platform_instance(platform)
            self.assertEqual(type(platform_instance).__name__, platform)

    def test_get_platform_instance_unknown_platform(self):
        """Test get_platform_instance for an unknown platform."""
        self.assertRaises(
            PlatformFailedError, self.worker.get_platform_instance,
            'TestPlatform')

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.download_statement')
    def test_evaluate_requests_platform(self, mock_download, mock_parse):
        """Test evaluate_platform with a platform based P2PSession."""
        mock_parse.return_value = (pd.DataFrame(), '')
        self.worker.evaluate_platform('Bondora')
        mock_download.assert_called_once()
        mock_parse.assert_called_once()

    @patch('easyp2p.p2p_worker.p2p_platforms.Iuvo.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Iuvo.download_statement')
    def test_evaluate_headless_selenium_platform(
            self, mock_download, mock_parse):
        """
        Test evaluate_platform with a platform based on P2PWebDriver in
        headless mode.
        """
        mock_parse.return_value = (pd.DataFrame(), '')
        self.worker.evaluate_platform('Iuvo')
        self.settings.headless = True
        mock_download.assert_called_once_with(True)
        mock_parse.assert_called_once()

    @patch('easyp2p.p2p_worker.p2p_platforms.Iuvo.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Iuvo.download_statement')
    def test_evaluate_non_headless_selenium_platform(
            self, mock_download, mock_parse):
        """
        Test evaluate_platform with a platform based on P2PWebDriver in
        non-headless mode.
        """
        mock_parse.return_value = (pd.DataFrame(), '')
        self.worker.settings.headless = False
        self.worker.evaluate_platform('Iuvo')
        mock_download.assert_called_once_with(False)
        mock_parse.assert_called_once()

    @patch('easyp2p.p2p_worker.p2p_platforms.Mintos.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Mintos.download_statement')
    def test_evaluate_captcha_platform(self, mock_download, mock_parse):
        """Test evaluate_platform with a platform which uses captchas."""
        mock_parse.return_value = (pd.DataFrame(), '')
        self.worker.evaluate_platform('Mintos')
        self.settings.headless = True
        mock_download.assert_called_once_with(False)
        mock_parse.assert_called_once()

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.download_statement')
    def test_evaluate_platform_download_fails(self, mock_download, mock_parse):
        """Test evaluate_platform if statement download fails."""
        self.settings.platforms = {'Bondora'}
        mock_download.side_effect = PlatformFailedError('Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.evaluate_platform,
            'Bondora')
        mock_download.assert_called_once()
        assert not mock_parse.called

    @patch('easyp2p.p2p_worker.write_results')
    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.download_statement')
    def test_appending_parser_results(
            self, mock_download, mock_parse, mock_writer):
        """Test appending parser results from an additional platform."""
        self.worker.df_result = pd.DataFrame([1, 2, 3])
        mock_parse.return_value = (pd.DataFrame([4, 5, 6]), '')
        mock_writer.return_value = True
        self.worker.settings.platforms = {'Bondora'}
        self.worker.run()
        mock_download.assert_called_once()
        mock_parse.assert_called_once()
        self.assertTrue(
            self.worker.df_result.equals(
                pd.DataFrame(
                    data=[1, 2, 3, 4, 5, 6], index=[0, 1, 2, 0, 1, 2])))

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.download_statement')
    def test_parse_statements_parser_error(self, mock_download, mock_parse):
        """Test parse_statements if the parser raises an error."""
        mock_parse.side_effect = PlatformFailedError('Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.evaluate_platform,
            'Bondora')
        mock_download.assert_called_once()
        mock_parse.assert_called_once()

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.parse_statement')
    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora.download_statement')
    @patch('easyp2p.p2p_worker.WorkerThread.signals.add_progress_text')
    def test_evaluate_platform_unknown_cf_type(
            self, mock_text, mock_download, mock_parse):
        """Test evaluate_platform if there are unknown cash flow types."""
        df_in = pd.DataFrame([1, 2, 3])
        mock_parse.return_value = (df_in, ('TestCF1', 'TestCF2'))
        df_out = self.worker.evaluate_platform('Bondora')
        mock_download.assert_called_once()
        mock_parse.assert_called_once()
        self.assertTrue(df_out.equals(df_in))
        mock_text.emit.assert_called_with(
            "Bondora: unknown cash flow type will be ignored in result: "
            "('TestCF1', 'TestCF2')", True)

    @patch('os.makedirs')
    def test_get_statement_location(self, mock_makedirs):
        """Test get_statement_location."""
        statement_location = self.worker.get_statement_location('Test')
        statement_dir = os.path.join(self.worker.settings.directory, 'test')
        self.assertEqual(
            statement_location,
            os.path.join(statement_dir, 'test_statement_20180901-20181231'))
        mock_makedirs.assert_called_once_with(statement_dir, exist_ok=True)

    @patch('easyp2p.p2p_worker.WorkerThread.signals.add_progress_text')
    @patch('easyp2p.p2p_worker.write_results')
    @patch('easyp2p.p2p_worker.WorkerThread.evaluate_platform')
    def test_run_no_results(
            self, mock_eval, mock_write_results, mock_text):
        """Test writing results when there were none."""
        mock_eval.side_effect = PlatformFailedError
        mock_write_results.return_value = False
        self.worker.run()
        mock_write_results.assert_called_once_with(
            self.worker.df_result, self.settings.output_file,
            self.settings.date_range)
        mock_text.emit.assert_called_with('No results available!', True)


if __name__ == "__main__":
    unittest.main()
