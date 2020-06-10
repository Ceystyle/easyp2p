# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module containing tests for P2PWebDriver class.

Most methods of the P2PWebDriver class rely on Selenium functionality and are
difficult to test individually. They are tested in test_download instead.

"""

import os
import shutil
import unittest.mock

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from easyp2p.p2p_chrome import P2PChrome
from easyp2p.p2p_webdriver import P2PWebDriver


class DownloadFinishedTests(unittest.TestCase):

    """Test the _download_finished method."""

    @unittest.mock.patch('easyp2p.p2p_chrome.Chrome.__init__')
    def setUp(self, _) -> None:
        """Create download directory."""
        self.platform = P2PWebDriver(
            'Test', False, EC.element_to_be_clickable((By.XPATH, 'xxx')),
            logout_url='xxx')
        self.download_dir = os.path.join(
            os.getcwd(), 'tests', 'test_download_finished')
        self.platform.driver = P2PChrome(self.download_dir, False)
        if not os.path.exists(self.platform.driver.download_directory):
            os.makedirs(self.platform.driver.download_directory)
        self.statement = os.path.join(
            os.getcwd(), 'tests', 'test_download_finished.xlsx')

        # Make sure self.statement does not exist
        if os.path.isfile(self.statement):
            os.remove(self.statement)

    def tearDown(self) -> None:
        """Delete download directory and statement file."""
        try:
            shutil.rmtree(self.download_dir)
            if os.path.isfile(self.statement):
                os.remove(self.statement)
        except OSError as err:
            print(f'Error: {err.filename} - {err.strerror}.')

    def test_no_crdownload_file(self):
        """Test return value if download does not start."""
        self.assertFalse(self.platform.download_finished(self.statement))
        self.assertFalse(os.path.isfile(self.statement))

    def test_success(self):
        """Test return value if download succeeds."""
        # Create a file in the download directory
        file = open(os.path.join(
            self.download_dir, 'test.xlsx'), 'w+')
        file.close()
        self.assertTrue(self.platform.download_finished(self.statement))
        self.assertTrue(os.path.isfile(self.statement))

    def test_download_does_not_finish(self):
        """Test return value if download starts but does not finish."""
        # Create a file in the download directory
        file = open(os.path.join(
            self.download_dir, 'test.crdownload'), 'w+')
        file.close()
        self.assertFalse(self.platform.download_finished(self.statement))
        self.assertFalse(os.path.isfile(self.statement))

    def test_non_empty_download_directory(self):
        """Test that error is raised when download directory is not empty."""
        # Create two files in the download directory
        file = open(os.path.join(
            self.download_dir, 'test1.xlsx'), 'w+')
        file.close()
        file = open(os.path.join(
            self.download_dir, 'test2.xlsx'), 'w+')
        file.close()
        self.assertRaises(
            RuntimeError, self.platform.download_finished, self.statement)
        self.assertFalse(os.path.isfile(self.statement))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(DownloadFinishedTests))
    result = runner.run(suite)
