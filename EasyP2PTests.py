# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

from datetime import date
import keyring
import sys
from typing import Tuple
import unittest

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest

from ui.main_window import MainWindow
from ui.progress_window import ProgressWindow
import p2p_platforms

app = QApplication(sys.argv)


class MainWindowTests(unittest.TestCase):
    """Test the main window of easyP2P"""
    def setUp(self) -> None:
        """Create the GUI"""
        self.form = MainWindow()
        self.message_box_open = False
        self.progress_window_open = False

    def set_test_dates(self) -> None:
        """Sets start and end dates in the GUI."""
        self.form.comboBox_start_month.setCurrentIndex(
            self.form.comboBox_start_month.findText('Sep'))
        self.form.comboBox_start_year.setCurrentIndex(
            self.form.comboBox_start_month.findText('2018'))
        self.form.comboBox_end_month.setCurrentIndex(
            self.form.comboBox_start_month.findText('Dez'))
        self.form.comboBox_end_year.setCurrentIndex(
            self.form.comboBox_start_month.findText('2018'))

    def test_defaults(self) -> None:
        """Test GUI in default state"""

        # All checkboxes are unchecked in default state
        self.assertFalse(self.form.checkBox_bondora.isChecked())
        self.assertFalse(self.form.checkBox_dofinance.isChecked())
        self.assertFalse(self.form.checkBox_estateguru.isChecked())
        self.assertFalse(self.form.checkBox_grupeer.isChecked())
        self.assertFalse(self.form.checkBox_iuvo.isChecked())
        self.assertFalse(self.form.checkBox_mintos.isChecked())
        self.assertFalse(self.form.checkBox_peerberry.isChecked())
        self.assertFalse(self.form.checkBox_robocash.isChecked())
        self.assertFalse(self.form.checkBox_select_all.isChecked())
        self.assertFalse(self.form.checkBox_swaper.isChecked())
        self.assertFalse(self.form.checkBox_twino.isChecked())
        #TODO: add tests for comboBoxes and output file name

    def test_select_all_platforms(self) -> None:
        """Test the Select All Platforms checkbox"""
        # Toggle the 'Select all platforms' checkbox
        self.form.checkBox_select_all.setChecked(True)

        # Test that all platforms are indeed selected
        self.assertTrue(self.form.checkBox_bondora.isChecked())
        self.assertTrue(self.form.checkBox_dofinance.isChecked())
        self.assertTrue(self.form.checkBox_estateguru.isChecked())
        self.assertTrue(self.form.checkBox_grupeer.isChecked())
        self.assertTrue(self.form.checkBox_iuvo.isChecked())
        self.assertTrue(self.form.checkBox_mintos.isChecked())
        self.assertTrue(self.form.checkBox_peerberry.isChecked())
        self.assertTrue(self.form.checkBox_robocash.isChecked())
        self.assertTrue(self.form.checkBox_select_all.isChecked())
        self.assertTrue(self.form.checkBox_swaper.isChecked())
        self.assertTrue(self.form.checkBox_twino.isChecked())

    def test_no_platform_selected(self) -> None:
        """Test clicking start without any selected platform"""
        # Push the start button without selecting any platform first
        QTimer.singleShot(500, self.is_message_box_open)
        self.form.pushButton_start.click()

        # Check that a warning message pops up
        self.assertTrue(self.message_box_open)

        # Check that the progress window did not open
        self.assertFalse(self.progress_window_open)
        
    def is_message_box_open(self) -> bool:
        """Helper method to determine if a QMessageBox is open."""
        allToplevelWidgets = QApplication.topLevelWidgets()
        for widget in allToplevelWidgets:
            if isinstance(widget, QMessageBox):
                self.message_box_open = True
                QTest.keyClick(widget, Qt.Key_Enter)

    def is_progress_window_open(self):
        """Helper method to determine if a ProgressWindow is open."""
        allToplevelWidgets = QApplication.topLevelWidgets()
        for widget in allToplevelWidgets:
            if isinstance(widget, ProgressWindow):
                self.progress_window_open = True


class ProgressWindowTests(unittest.TestCase):
    """Test the progress window of easyP2P"""
    def setup_gui(self):
        self.form = ProgressWindow()

    def test_defaults(self):
        self.setup_gui()
        self.assertEqual(self.form.progressBar.value(), 0)
        self.assertEqual(self.form.progressText.isReadOnly(), True)
        self.assertEqual(self.form.progressText.toPlainText(), '')
        self.assertEqual(self.form.pushButton_ok.isEnabled(), False)
        self.assertEqual(self.form.pushButton_abort.isEnabled(), True)


class P2PTests(unittest.TestCase):
    """Test p2p_platforms"""
    def setUp(self):
        """Initializes the default arguments for p2p_platforms."""
        self.start_date = date(2018, 9, 1)
        self.end_date = date(2018, 12, 31)

    def get_credentials_from_keyring(self, platform: str) -> Tuple[str, str]:
        """
        Helper function to get credentials from the keyring.

        Args:
            platform (str): Name of the P2P platform

        Returns:
            Tuple[str, str]: (username, password) for the P2P platform or None
                if the platform was not found in the keyring.

        """
        if keyring.get_keyring():
            try:
                username = keyring.get_password(platform, 'username')
                password = keyring.get_password(platform, username)
            except TypeError:
                self.skipTest(
                    'No credentials for {0} in the keyring.'.format(platform))

        return (username, password)

    def test_open_selenium_bondora(self) -> None:
        """Test open_selenium_bondora function"""
        credentials = self.get_credentials_from_keyring('Bondora')
        self.assertTrue(p2p_platforms.open_selenium_bondora(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_dofinance(self):
        """Test open_selenium_dofinance function"""
        credentials = self.get_credentials_from_keyring('DoFinance')
        self.assertTrue(p2p_platforms.open_selenium_dofinance(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_estateguru(self):
        """Test open_selenium_estateguru function"""
        credentials = self.get_credentials_from_keyring('Estateguru')
        self.assertTrue(p2p_platforms.open_selenium_estateguru(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_grupeer(self):
        """Test open_selenium_grupeer function"""
        credentials = self.get_credentials_from_keyring('Grupeer')
        self.assertTrue(p2p_platforms.open_selenium_grupeer(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_iuvo(self):
        """Test open_selenium_iuvo function"""
        credentials = self.get_credentials_from_keyring('Iuvo')
        self.assertTrue(p2p_platforms.open_selenium_iuvo(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_mintos(self):
        """Test open_selenium_mintos function"""
        credentials = self.get_credentials_from_keyring('Mintos')
        self.assertTrue(p2p_platforms.open_selenium_mintos(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_peerberry(self):
        """Test open_selenium_peerberry function"""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        self.assertTrue(p2p_platforms.open_selenium_peerberry(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_robocash(self):
        """Test open_selenium_robocash function"""
        credentials = self.get_credentials_from_keyring('Robocash')
        self.assertTrue(p2p_platforms.open_selenium_robocash(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_swaper(self):
        """Test open_selenium_swaper function"""
        credentials = self.get_credentials_from_keyring('Swaper')
        self.assertTrue(p2p_platforms.open_selenium_swaper(
            self.start_date, self.end_date, credentials))

    def test_open_selenium_twino(self):
        """Test open_selenium_twino function"""
        credentials = self.get_credentials_from_keyring('Twino')
        self.assertTrue(p2p_platforms.open_selenium_twino(
            self.start_date, self.end_date, credentials))

if __name__ == "__main__":
    unittest.main()
