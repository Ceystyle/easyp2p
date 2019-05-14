# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for p2p_worker."""

from datetime import date
import os
from pathlib import Path
import unittest.mock

import pandas as pd

from easyp2p.p2p_settings import Settings
from easyp2p.p2p_worker import WorkerThread, PlatformFailedError
from easyp2p.p2p_webdriver import WebDriverNotFound
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

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @unittest.mock.patch('easyp2p.p2p_worker.P2PWebDriver')
    def test_download_statements(self, mock_webdriver, mock_bondora):
        """Test download_statements with Bondora."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        self.worker.download_statements('Bondora', bondora, 'test')
        mock_webdriver.assert_called_once_with('test', True)
        bondora.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('test', True), ('TestUser', 'TestPass'))

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_download_statements_missing_credentials(
            self, mock_bondora):
        """Test download_statements if credentials are missing."""
        self.worker.credentials['Bondora'] = None
        bondora = mock_bondora(self.settings.date_range, 'test')
        self.assertRaises(
            PlatformFailedError, self.worker.download_statements,
            'Bondora', bondora, 'test')

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @unittest.mock.patch('easyp2p.p2p_worker.P2PWebDriver')
    def test_download_statements_download_fails(
            self, mock_webdriver, mock_bondora):
        """Test download_statements if platform download fails."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.download_statement.side_effect = RuntimeError('Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.download_statements,
            'Bondora', bondora, 'test')
        mock_webdriver.assert_called_once_with('test', True)
        bondora.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('test', True), ('TestUser', 'TestPass'))

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @unittest.mock.patch('easyp2p.p2p_worker.P2PWebDriver')
    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.abort_easyp2p')
    def test_download_statements_no_webdriver(
            self, mock_abort, mock_webdriver, mock_bondora):
        """Test download_statements if webdriver cannot be found."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.download_statement.side_effect = WebDriverNotFound('Test error')
        self.worker.download_statements('Bondora', bondora, 'test')
        mock_webdriver.assert_called_once_with('test', True)
        bondora.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('test', True), ('TestUser', 'TestPass'))
        mock_abort.emit.assert_called_once_with('Test error')

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @unittest.mock.patch('easyp2p.p2p_worker.P2PWebDriver')
    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.add_progress_text')
    def test_download_statements_runtime_warning(
            self, mock_text, mock_webdriver, mock_bondora):
        """Test download_statements if platform download raises a warning."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.download_statement.side_effect = RuntimeWarning('Test warning')
        self.worker.download_statements('Bondora', bondora, 'test')
        mock_webdriver.assert_called_once_with('test', True)
        bondora.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('test', True), ('TestUser', 'TestPass'))
        mock_text.emit.assert_called_with('Test warning', self.worker.RED)

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Iuvo')
    @unittest.mock.patch('easyp2p.p2p_worker.P2PWebDriver')
    def test_download_statements_iuvo(self, mock_webdriver, mock_iuvo):
        """Test download_statements with Iuvo."""
        iuvo = mock_iuvo(self.settings.date_range, 'test')
        self.worker.download_statements('Iuvo', iuvo, 'test')
        mock_webdriver.assert_called_once_with('test', False)
        iuvo.download_statement.assert_called_once_with(
            mock_webdriver().__enter__('test', False), ('TestUser', 'TestPass'))

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
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

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    def test_parse_statements_parser_error(self, mock_bondora):
        """Test parse_statements if the parser raises an error."""
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.parse_statement.side_effect = RuntimeError('Test error')
        self.assertRaisesRegex(
            PlatformFailedError, 'Test error', self.worker.parse_statements,
            'Bondora', bondora)

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_platforms.Bondora')
    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.add_progress_text')
    def test_parse_statements_unknown_cf_type(self, mock_text, mock_bondora):
        """Test parse_statements if there are unknown cashflow types."""
        self.worker.df_result = pd.DataFrame([1, 2, 3])
        bondora = mock_bondora(self.settings.date_range, 'test')
        bondora.parse_statement.return_value = (
            pd.DataFrame([4, 5, 6]), {'TestCF1', 'TestCF2'})
        self.worker.parse_statements('Bondora', bondora)
        bondora.parse_statement.assert_called_once_with()
        self.assertTrue(
            self.worker.df_result.equals(
                pd.DataFrame(
                    data=[1, 2, 3, 4, 5, 6], index=[0, 1, 2, 0, 1, 2])))
        mock_text.emit.assert_called_with(
            "Bondora: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: "
            "{'TestCF1', 'TestCF2'}", self.worker.RED)

    @unittest.mock.patch('easyp2p.p2p_worker.os.makedirs')
    @unittest.mock.patch('easyp2p.p2p_worker.os.path.isdir')
    def test_set_download_directory_not_exists(
            self, mock_isdir, mock_makedirs):
        """Test set_download_directory if download directory does not exist."""
        mock_isdir.return_value = False
        statement_without_suffix, download_directory = \
            self.worker.set_download_directory('TestPlatform')
        self.assertEqual(statement_without_suffix, os.path.join(
            Path.home(), '.easyp2p', 'testplatform',
            'testplatform_statement_20180901-20181231'))
        self.assertEqual(download_directory, os.path.join(
            Path.home(), '.easyp2p', 'testplatform', 'active'))
        mock_makedirs.assert_called_once_with(download_directory)

    @unittest.mock.patch('easyp2p.p2p_worker.os.remove')
    @unittest.mock.patch('easyp2p.p2p_worker.os.listdir')
    @unittest.mock.patch('easyp2p.p2p_worker.os.path.isdir')
    def test_set_download_directory_exists_empty(
            self, mock_isdir, mock_listdir, mock_remove):
        """
        Test set_download_directory if download directory exists and is empty.
        """
        mock_isdir.return_value = True
        mock_listdir.return_value = []
        statement_without_suffix, download_directory = \
            self.worker.set_download_directory('TestPlatform')
        self.assertEqual(statement_without_suffix, os.path.join(
            Path.home(), '.easyp2p', 'testplatform',
            'testplatform_statement_20180901-20181231'))
        self.assertEqual(download_directory, os.path.join(
            Path.home(), '.easyp2p', 'testplatform', 'active'))
        mock_listdir.assert_called_once_with(path=download_directory)
        self.assertFalse(mock_remove.called)

    @unittest.mock.patch('easyp2p.p2p_worker.os.remove')
    @unittest.mock.patch('easyp2p.p2p_worker.os.listdir')
    @unittest.mock.patch('easyp2p.p2p_worker.os.path.isdir')
    def test_set_download_directory_exists_not_empty(
            self, mock_isdir, mock_listdir, mock_remove):
        """
        Test set_download_directory if non-empty download directory exists.
        """
        mock_isdir.return_value = True
        mock_listdir.return_value = ['file1', 'file2']
        statement_without_suffix, download_directory = \
            self.worker.set_download_directory('TestPlatform')
        self.assertEqual(statement_without_suffix, os.path.join(
            Path.home(), '.easyp2p', 'testplatform',
            'testplatform_statement_20180901-20181231'))
        self.assertEqual(download_directory, os.path.join(
            Path.home(), '.easyp2p', 'testplatform', 'active'))
        mock_listdir.assert_called_once_with(path=download_directory)
        self.assertEqual(
            mock_remove.call_args_list, [
                unittest.mock.call(os.path.join(download_directory, 'file1')),
                unittest.mock.call(os.path.join(download_directory, 'file2'))])

    @unittest.mock.patch('easyp2p.p2p_worker.p2p_parser.write_results')
    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.download_statements')
    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.parse_statements')
    @unittest.mock.patch(
        'easyp2p.p2p_worker.WorkerThread.set_download_directory')
    def test_run(
            self, mock_set_dldir, mock_parse, mock_download,
            mock_write_results):
        """Test running all platforms."""
        mock_set_dldir.return_value = 'test_statement', 'test_dldir'
        self.worker.run()

        expected_download_args = []
        expected_parse_args = []
        for platform in PLATFORMS:
            # TODO: replace ANY by real platform instance
            expected_download_args.append(unittest.mock.call(
                platform, unittest.mock.ANY, 'test_dldir'))
            expected_parse_args.append(unittest.mock.call(
                platform, unittest.mock.ANY))
        self.assertEqual(mock_download.call_args_list, expected_download_args)
        self.assertEqual(mock_parse.call_args_list, expected_parse_args)
        mock_write_results.assert_called_once_with(
            self.worker.df_result, self.settings.output_file)

    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.add_progress_text')
    @unittest.mock.patch('easyp2p.p2p_worker.p2p_parser.write_results')
    @unittest.mock.patch('easyp2p.p2p_worker.WorkerThread.download_statements')
    @unittest.mock.patch(
        'easyp2p.p2p_worker.WorkerThread.set_download_directory')
    def test_run_no_results(
            self, mock_set_dldir, mock_download,
            mock_write_results, mock_text):
        """Test writing results when there were none."""
        mock_set_dldir.return_value = 'test_statement', 'test_dldir'
        mock_download.side_effect = PlatformFailedError
        mock_write_results.return_value = False
        self.worker.run()
        mock_write_results.assert_called_once_with(
            self.worker.df_result, self.settings.output_file)
        mock_text.emit.assert_called_with(
            'Keine Ergebnisse vorhanden', self.worker.RED)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(WorkerTests)
    result = runner.run(suite)
