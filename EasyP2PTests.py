# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

from datetime import date
from pathlib import Path
import sys
from typing import Tuple
import unittest

import keyring
import pandas as pd
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

    def are_files_equal(self, file1: str, file2: str) -> bool:
        """
        Helper method to determine if two files are equal.

        Args:
            file1 (str): Name including path of first file
            file2 (str): Name including path of second file

        Returns:
            bool: True if the files are equal, False if not or if at least one
            of the files does not exist

        """
        if Path(file1).suffix == Path(file2).suffix:
            file_format = Path(file1).suffix
        else:
            return False

        try:
            if file_format == '.csv':
                df1 = pd.read_csv(file1)
                df2 = pd.read_csv(file2)
            elif file_format == '.xlsx':
                df1 = pd.read_excel(file1)
                df2 = pd.read_excel(file2)
            else:
                raise TypeError('Unknown file format!')
        except FileNotFoundError:
            return False

        return df1.equals(df2)

    def get_credentials_from_keyring(self, platform: str) -> Tuple[str, str]:
        """
        Helper method to get credentials from the keyring.

        Args:
            platform (str): Name of the P2P platform

        Returns:
            Tuple[str, str]: (username, password) for the P2P platform

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
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            'tests/results/result_test_open_selenium_bondora.csv'))

    def test_open_selenium_dofinance(self):
        """Test open_selenium_dofinance function"""
        credentials = self.get_credentials_from_keyring('DoFinance')
        self.assertTrue(p2p_platforms.open_selenium_dofinance(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/dofinance_statement.xlsx',
            'tests/results/result_test_open_selenium_dofinance.xlsx'))

    def test_open_selenium_estateguru(self):
        """Test open_selenium_estateguru function"""
        credentials = self.get_credentials_from_keyring('Estateguru')
        self.assertTrue(p2p_platforms.open_selenium_estateguru(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/estateguru_statement.csv',
            'tests/results/result_test_open_selenium_estateguru.csv'))

    def test_open_selenium_grupeer(self):
        """Test open_selenium_grupeer function"""
        credentials = self.get_credentials_from_keyring('Grupeer')
        self.assertTrue(p2p_platforms.open_selenium_grupeer(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/grupeer_statement.xlsx',
            'tests/results/result_test_open_selenium_grupeer.xlsx'))

    def test_open_selenium_iuvo(self):
        """Test open_selenium_iuvo function"""
        credentials = self.get_credentials_from_keyring('Iuvo')
        self.assertTrue(p2p_platforms.open_selenium_iuvo(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/iuvo_statement.csv',
            'tests/results/result_test_open_selenium_iuvo.csv'))

    def test_open_selenium_mintos(self):
        """Test open_selenium_mintos function"""
        credentials = self.get_credentials_from_keyring('Mintos')
        self.assertTrue(p2p_platforms.open_selenium_mintos(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/mintos_statement.xlsx',
            'tests/results/result_test_open_selenium_mintos.xlsx'))

    def test_open_selenium_peerberry(self):
        """Test open_selenium_peerberry function"""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        self.assertTrue(p2p_platforms.open_selenium_peerberry(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/peerberry_statement.csv',
            'tests/results/result_test_open_selenium_peerberry.csv'))

    def test_open_selenium_robocash(self):
        """Test open_selenium_robocash function"""
        credentials = self.get_credentials_from_keyring('Robocash')
        self.assertTrue(p2p_platforms.open_selenium_robocash(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/robocash_statement.xlsx',
            'tests/results/result_test_open_selenium_robocash.xlsx'))

    def test_open_selenium_swaper(self):
        """Test open_selenium_swaper function"""
        credentials = self.get_credentials_from_keyring('Swaper')
        self.assertTrue(p2p_platforms.open_selenium_swaper(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/swaper_statement.xlsx',
            'tests/results/result_test_open_selenium_swaper.xlsx'))

    def test_open_selenium_twino(self):
        """Test open_selenium_twino function"""
        credentials = self.get_credentials_from_keyring('Twino')
        self.assertTrue(p2p_platforms.open_selenium_twino(
            self.start_date, self.end_date, credentials))
        self.assertTrue(self.are_files_equal(
            'p2p_downloads/twino_statement.xlsx',
            'tests/results/result_test_open_selenium_twino.xlsx'))


if __name__ == "__main__":
    unittest.main()
