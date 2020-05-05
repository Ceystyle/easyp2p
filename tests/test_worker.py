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
from tests import PLATFORMS


class WorkerTests(unittest.TestCase):

    """Contains all p2p_worker tests."""

    def setUp(self) -> None:
        """Initialize the WorkerThread."""
        self.settings = Settings(
            (date(2018, 9, 1), date(2018, 12, 31)),
            os.path.join(os.getcwd(), 'test.xlsx'))
        self.settings.platforms = set(PLATFORMS)
        self.worker = WorkerThread(self.settings)
        self.worker.signals.abort = False

    def test_get_platform_instance(self):
        """Test get_platform_instance for all supported platforms."""
        for platform in PLATFORMS:
            platform_instance = self.worker.get_platform_instance(platform)
            self.assertEqual(type(platform_instance).__name__, platform)

    def test_get_platform_instance_unknown_platform(self):
        """Test get_platform_instance for an unknown platform."""
        self.assertRaises(
            PlatformFailedError, self.worker.get_platform_instance,
            'TestPlatform')

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_download_statements(self, mock_bondora):
        """Test download_statements with Bondora."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        self.worker.download_statements(bondora)
        bondora.download_statement.assert_called_once_with(True)

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_download_statements_download_fails(self, mock_bondora):
        """Test download_statements if platform download fails."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.download_statement.side_effect = PlatformFailedError(
            'Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.download_statements,
            bondora)
        bondora.download_statement.assert_called_once_with(True)

    @patch('easyp2p.p2p_worker.p2p_platforms.Iuvo')
    def test_download_statements_iuvo(self, mock_iuvo):
        """Test download_statements with Iuvo."""
        iuvo = mock_iuvo(self.settings.date_range, 'test')
        iuvo.name = 'Iuvo'
        self.worker.download_statements(iuvo)
        iuvo.download_statement.assert_called_once_with(False)

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_parse_statements(self, mock_bondora):
        """Test parse_statements for Bondora."""
        self.worker.df_result = pd.DataFrame([1, 2, 3])
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.parse_statement.return_value = (pd.DataFrame([4, 5, 6]), '')
        self.worker.parse_statements(bondora)
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
            bondora)

    @patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @patch('easyp2p.p2p_worker.WorkerThread.signals.add_progress_text')
    def test_parse_statements_unknown_cf_type(self, mock_text, mock_bondora):
        """Test parse_statements if there are unknown cash flow types."""
        self.worker.df_result = pd.DataFrame([1, 2, 3])
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.name = 'Bondora'
        bondora.parse_statement.return_value = (
            pd.DataFrame([4, 5, 6]), ['TestCF1', 'TestCF2'])
        self.worker.parse_statements(bondora)
        bondora.parse_statement.assert_called_once_with()
        self.assertTrue(
            self.worker.df_result.equals(
                pd.DataFrame(
                    data=[1, 2, 3, 4, 5, 6], index=[0, 1, 2, 0, 1, 2])))
        mock_text.emit.assert_called_with(
            "Bondora: unknown cash flow type will be ignored in result: "
            "['TestCF1', 'TestCF2']", True)

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
