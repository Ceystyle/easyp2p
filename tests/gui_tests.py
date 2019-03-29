# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all GUI tests for easyp2p."""

import sys
import unittest

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest

from .context import MainWindow, ProgressWindow

PLATFORMS = {
    'Bondora': 'csv',
    'DoFinance': 'xlsx',
    'Estateguru': 'csv',
    'Grupeer': 'xlsx',
    'Iuvo': 'xlsx',
    'Mintos': 'xlsx',
    'PeerBerry': 'csv',
    'Robocash': 'xls',
    'Swaper': 'xlsx',
    'Twino': 'xlsx'}

app = QApplication(sys.argv)


class MainWindowTests(unittest.TestCase):

    """Test the main window of easyp2p."""

    def setUp(self) -> None:
        """Create the GUI."""
        self.form = MainWindow()
        self.message_box_open = False
        self.progress_window_open = False

    def set_test_dates(self) -> None:
        """Set start and end dates in the GUI."""
        self.form.comboBox_start_month.setCurrentIndex(
            self.form.comboBox_start_month.findText('Sep'))
        self.form.comboBox_start_year.setCurrentIndex(
            self.form.comboBox_start_month.findText('2018'))
        self.form.comboBox_end_month.setCurrentIndex(
            self.form.comboBox_start_month.findText('Jan'))
        self.form.comboBox_end_year.setCurrentIndex(
            self.form.comboBox_start_month.findText('2019'))

    def test_defaults(self) -> None:
        """Test GUI in default state."""

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
        # TODO: add tests for comboBoxes and output file name

    def test_select_all_platforms(self) -> None:
        """Test the Select All Platforms checkbox."""
        # Toggle the 'Select all platforms' checkbox
        self.form.checkBox_select_all.setChecked(True)

        # Test that all platform check boxes are checked
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

        # Test if the platform list is correct
        self.assertEqual(self.form.platforms, PLATFORMS.keys())

    def test_no_platform_selected(self) -> None:
        """Test clicking start without any selected platform."""
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

    """Test the progress window of easyp2p."""

    def setup_gui(self):
        """Initialize ProgressWindow."""
        self.form = ProgressWindow()

    def test_defaults(self):
        """Test default behaviour of ProgressWindow."""
        self.setup_gui()
        self.assertEqual(self.form.progressBar.value(), 0)
        self.assertEqual(self.form.progressText.isReadOnly(), True)
        self.assertEqual(self.form.progressText.toPlainText(), '')
        self.assertEqual(self.form.pushButton_ok.isEnabled(), False)
        self.assertEqual(self.form.pushButton_abort.isEnabled(), True)


if __name__ == "__main__":
    unittest.main()
