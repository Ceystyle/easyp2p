# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""
Module containing tests for P2PPlatform class.

Most methods of the P2PPlatform class rely on Selenium functionality and are
difficult to test individually. They are tested in test_download instead.

"""

from datetime import date
import os
import shutil
import unittest

import easyp2p.p2p_platform as p2p_platform


class CalenderClickTests(unittest.TestCase):

    """Tests for the P2PPlatform class."""

    def test_get_calendar_clicks_positive(self):
        """Test _get_calendar_clicks if target date > start date."""
        clicks = p2p_platform._get_calendar_clicks(
            date(2018, 4, 5), date(2017, 9, 27))
        self.assertEqual(clicks, 7)

    def test_get_calendar_clicks_negative(self):
        """Test _get_calendar_clicks if target date < start date."""
        clicks = p2p_platform._get_calendar_clicks(
            date(2016, 4, 5), date(2017, 9, 27))
        self.assertEqual(clicks, -17)

    def test_get_calendar_clicks_zero(self):
        """Test _get_calendar_clicks if target date == start date."""
        clicks = p2p_platform._get_calendar_clicks(
            date(2017, 9, 5), date(2017, 9, 27))
        self.assertEqual(clicks, 0)


class DownloadFinishedTests(unittest.TestCase):

    def setUp(self) -> None:
        """Create download directory."""
        self.download_directory = os.path.join(
            os.getcwd(), 'tests', 'test_download_finished')
        if not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)
        self.statement = os.path.join(
            os.getcwd(), 'tests', 'test_download_finished.xlsx')

        # Make sure self.statement does not exist
        if os.path.isfile(self.statement):
            os.remove(self.statement)

    def tearDown(self) -> None:
        """Delete download directory and statement file."""
        try:
            shutil.rmtree(self.download_directory)
            if os.path.isfile(self.statement):
                os.remove(self.statement)
        except OSError as err:
            print('Error: {} - {}.'.format(err.filename, err.strerror))

    def test_no_crdownload_file(self):
        """Test return value if download does not start."""
        self.assertFalse(p2p_platform._download_finished(
            self.statement, self.download_directory))
        self.assertFalse(os.path.isfile(self.statement))

    def test_success(self):
        """Test return value if download succeeds."""
        # Create a file in the download directory
        file = open(os.path.join(self.download_directory, 'test.xlsx'), 'w+')
        file.close()
        self.assertTrue(p2p_platform._download_finished(
            self.statement, self.download_directory))
        self.assertTrue(os.path.isfile(self.statement))

    def test_download_does_not_finish(self):
        """Test return value if download starts but does not finish."""
        # Create a file in the download directory
        file = open(
            os.path.join(self.download_directory, 'test.crdownload'), 'w+')
        file.close()
        self.assertFalse(p2p_platform._download_finished(
            self.statement, self.download_directory))
        self.assertFalse(os.path.isfile(self.statement))

    def test_non_empty_download_directory(self):
        """Test that error is raised when download directory is not empty."""
        # Create two files in the download directory
        file = open(
            os.path.join(self.download_directory, 'test1.xlsx'), 'w+')
        file.close()
        file = open(
            os.path.join(self.download_directory, 'test2.xlsx'), 'w+')
        file.close()
        self.assertRaises(RuntimeError, p2p_platform._download_finished,
            self.statement, self.download_directory)
        self.assertFalse(os.path.isfile(self.statement))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(CalenderClickTests))
    suite.addTests(loader.loadTestsFromTestCase(DownloadFinishedTests))
    result = runner.run(suite)