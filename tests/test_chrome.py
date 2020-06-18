#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module containing all tests for the P2PChrome class.
"""
import logging
import unittest.mock

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType

from easyp2p.p2p_chrome import P2PChrome
from easyp2p.p2p_signals import PlatformFailedError


class P2PChromeTests(unittest.TestCase):
    """Test P2PChrome if Chrome, Chromium or Chromedriver are not available."""

    @classmethod
    def setUpClass(cls) -> None:
        logging.disable(logging.CRITICAL)
        cls.chromium_path = ChromeDriverManager(
            chrome_type=ChromeType.CHROMIUM).install()

    @unittest.mock.patch('easyp2p.p2p_chrome.ChromeDriverManager.install')
    def test_no_chromedriver(self, mock_driver_install):
        """
        Test that PlatformFailedError is raised if ChromeDriver cannot be found.
        """
        mock_driver_install.side_effect = Exception
        self.assertRaises(PlatformFailedError, P2PChrome, 'sample_dir', True)

    @unittest.mock.patch('easyp2p.p2p_chrome.ChromeDriverManager.install')
    def test_no_chrome_no_chromium(self, mock_driver_install):
        """
        Test that PlatformFailedError is raised if neither Chrome nor Chromium
        are installed.
        """
        mock_driver_install.side_effect = ValueError
        self.assertRaises(PlatformFailedError, P2PChrome, 'sample_dir', True)

    @unittest.mock.patch('easyp2p.p2p_chrome.ChromeDriverManager.install')
    def test_no_chrome_but_chromium(self, mock_driver_install):
        """
        Test that P2PChrome initialization is successful if Chrome is not
        installed, but Chromium is.
        """
        mock_driver_install.side_effect = [ValueError, self.chromium_path]
        driver = P2PChrome('sample_dir', True)
        self.assertEqual('chrome', driver.name)
        driver.close()


if __name__ == "__main__":
    unittest.main()
