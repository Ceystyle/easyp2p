# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for p2p_worker."""

from datetime import date
import os
import unittest
from unittest import mock
from unittest.mock import patch

import pandas as pd
from selenium.common.exceptions import WebDriverException

from easyp2p.p2p_settings import Settings
from easyp2p.p2p_signals import PlatformFailedError
from easyp2p.platforms.bondora import Bondora
from easyp2p.p2p_worker import WorkerThread
from tests import PLATFORMS


class WorkerTests(unittest.TestCase):

    """Contains all p2p_worker tests."""

    def setUp(self) -> None:
        """Initialize the WorkerThread."""
        self.settings = Settings(
            (date(2018, 9, 1), date(2018, 12, 31)),
            os.path.join(os.getcwd(), 'test.xlsx'))
        self.settings.platforms = set(PLATFORMS)
        self.credentials = dict()
        for platform in PLATFORMS:
            self.credentials[platform] = ('TestUser', 'TestPass')
        self.worker = WorkerThread(self.settings, self.credentials)
        self.worker.signals.abort = False

    def test_get_platform_instance(self):
        """Test get_platform_instance for all supported platforms."""
        for platform in PLATFORMS:
            platform_instance = self.worker.get_platform_instance(
                platform, 'test_statement')
            self.assertEqual(type(platform_instance).__name__, platform)

    def test_get_platform_instance_unknown_platform(self):
        """Test get_platform_instance for an unknown platform."""
        self.assertRaises(
            PlatformFailedError, self.worker.get_platform_instance,
            'TestPlatform', 'test_statement')

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @patch('easyp2p.p2p_worker.P2PWebDriver')
    @patch('easyp2p.p2p_worker.tempfile.TemporaryDirectory')
    def test_download_statements(
            self, mock_tempdir, mock_webdriver, mock_bondora):
        """Test download_statements with Bondora."""
        mock_tempdir().__enter__.return_value = '/tmp/test'
        bondora = mock_bondora(self.settings.date_range, 'test')
        self.worker.download_statements('Bondora', bondora)
        mock_webdriver.assert_called_once_with(
            '/tmp/test', True, self.worker.signals)
        bondora.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('/tmp/test', True),
            ('TestUser', 'TestPass'))

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_download_statements_missing_credentials(
            self, mock_bondora):
        """Test download_statements if credentials are missing."""
        self.worker.credentials['Bondora'] = None
        bondora = mock_bondora(self.settings.date_range, 'test')
        self.assertRaises(
            PlatformFailedError, self.worker.download_statements,
            'Bondora', bondora)

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @patch('easyp2p.p2p_worker.P2PWebDriver')
    @patch('easyp2p.p2p_worker.tempfile.TemporaryDirectory')
    def test_download_statements_download_fails(
            self, mock_tempdir, mock_webdriver, mock_bondora):
        """Test download_statements if platform download fails."""
        mock_tempdir().__enter__.return_value = '/tmp/test'
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.download_statement.side_effect = PlatformFailedError(
            'Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.download_statements,
            'Bondora', bondora)
        mock_webdriver.assert_called_once_with(
            '/tmp/test', True, self.worker.signals)
        bondora.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('/tmp/test', True),
            ('TestUser', 'TestPass'))

    # TODO: this test needs more work
    # @patch('easyp2p.p2p_worker.P2PWebDriver.Chrome.__init__')
    # @patch('easyp2p.p2p_worker.WorkerThread.signals.end_easyp2p')
    # def test_download_statements_no_webdriver(
    #         self, mock_end_easyp2p, mock_chrome):
    #     """Test download_statements if webdriver cannot be found."""
    #     bondora = Bondora(self.settings.date_range, 'test')
    #     mock_chrome.side_effect = WebDriverException
    #     self.worker.download_statements('Bondora', bondora)
    #     self.assertTrue(mock_end_easyp2p.emit.called)

    @patch('easyp2p.p2p_worker.p2p_platforms.Iuvo')
    @patch('easyp2p.p2p_worker.P2PWebDriver')
    @patch('easyp2p.p2p_worker.tempfile.TemporaryDirectory')
    def test_download_statements_iuvo(
            self, mock_tempdir, mock_webdriver, mock_iuvo):
        """Test download_statements with Iuvo."""
        mock_tempdir().__enter__.return_value = '/tmp/test'
        iuvo = mock_iuvo(self.settings.date_range, 'test')
        self.worker.download_statements('Iuvo', iuvo)
        mock_webdriver.assert_called_once_with(
            '/tmp/test', False, self.worker.signals)
        iuvo.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('/tmp/test', False),
            ('TestUser', 'TestPass'))

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_parse_statements(self, mock_bondora):
        """Test parse_statements for Bondora."""
        self.worker.df_result = pd.DataFrame([1, 2, 3])
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.parse_statement.return_value = (pd.DataFrame([4, 5, 6]), '')
        self.worker.parse_statements('Bondora', bondora)
        bondora.parse_statement.assert_called_once_with()
        self.assertTrue(
            self.worker.df_result.equals(
                pd.DataFrame(
                    data=[1, 2, 3, 4, 5, 6], index=[0, 1, 2, 0, 1, 2])))

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_parse_statements_parser_error(self, mock_bondora):
        """Test parse_statements if the parser raises an error."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.parse_statement.side_effect = RuntimeError('Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.parse_statements,
            'Bondora', bondora)

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @patch('easyp2p.p2p_worker.WorkerThread.signals.add_progress_text')
    def test_parse_statements_unknown_cf_type(self, mock_text, mock_bondora):
        """Test parse_statements if there are unknown cashflow types."""
        self.worker.df_result = pd.DataFrame([1, 2, 3])
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.parse_statement.return_value = (
            pd.DataFrame([4, 5, 6]), ['TestCF1', 'TestCF2'])
        self.worker.parse_statements('Bondora', bondora)
        bondora.parse_statement.assert_called_once_with()
        self.assertTrue(
            self.worker.df_result.equals(
                pd.DataFrame(
                    data=[1, 2, 3, 4, 5, 6], index=[0, 1, 2, 0, 1, 2])))
        mock_text.emit.assert_called_with(
            "Bondora: unknown cash flow type will be ignored in result: "
            "['TestCF1', 'TestCF2']", True)

    @patch('easyp2p.p2p_worker.write_results')
    @patch('easyp2p.p2p_worker.WorkerThread.download_statements')
    @patch('easyp2p.p2p_worker.WorkerThread.parse_statements')
    def test_run(
            self, mock_parse, mock_download, mock_write_results):
        """Test running all platforms."""
        self.worker.run()
        for platform in PLATFORMS:
            # TODO: replace ANY by real platform instance
            self.assertTrue(unittest.mock.call(
                platform, unittest.mock.ANY) in mock_download.call_args_list)
            self.assertTrue(unittest.mock.call(
                platform, unittest.mock.ANY) in mock_parse.call_args_list)
        self.assertEqual(len(mock_download.call_args_list), len(PLATFORMS))
        self.assertEqual(len(mock_parse.call_args_list), len(PLATFORMS))
        mock_write_results.assert_called_once_with(
            self.worker.df_result, self.settings.output_file,
            self.settings.date_range)

    @patch('easyp2p.p2p_worker.WorkerThread.signals.add_progress_text')
    @patch('easyp2p.p2p_worker.write_results')
    @patch('easyp2p.p2p_worker.WorkerThread.download_statements')
    def test_run_no_results(
            self, mock_download, mock_write_results, mock_text):
        """Test writing results when there were none."""
        mock_download.side_effect = PlatformFailedError
        mock_write_results.return_value = False
        self.worker.run()
        mock_write_results.assert_called_once_with(
            self.worker.df_result, self.settings.output_file,
            self.settings.date_range)
        mock_text.emit.assert_called_with('No results available!', True)


if __name__ == "__main__":
    unittest.main()
