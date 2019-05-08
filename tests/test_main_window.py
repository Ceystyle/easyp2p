# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the main window of easyp2p."""

import calendar
from datetime import date
import functools
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QCheckBox, QLineEdit
from PyQt5.QtTest import QTest

from easyp2p.platforms import Bondora
from easyp2p.ui.main_window import MainWindow
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.settings_window import SettingsWindow
import tests.utils as utils

APP = QApplication(sys.argv)


class MainWindowTests(unittest.TestCase):

    """Test the main window of easyp2p."""

    def setUp(self) -> None:
        """Create the GUI."""
        self.form = MainWindow()
        self.test_results = []

    def test_defaults(self) -> None:
        """Test GUI in default state."""

        # All check boxes are unchecked in default state
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertFalse(check_box.isChecked())

        # Check if output file name is set correctly
        date_range = self.form.get_date_range()
        self.assertEqual(
            self.form.line_edit_output_file.text(), os.path.join(
                Path.home(), 'P2P_Ergebnisse_{0}-{1}.xlsx'.format(
                    date_range[0].strftime('%d%m%Y'),
                    date_range[1].strftime('%d%m%Y'))))

        # Check if combo boxes are set correctly
        date_range = self.form.get_date_range()
        today = date.today()
        if today.month > 1:
            self.assertEqual(date_range, (date(today.year, today.month - 1, 1),
                date(today.year, today.month - 1,
                    calendar.monthrange(today.year, today.month - 1)[1])))
        else:
            self.assertEqual(date_range, (date(today.year - 1, 12, 1), date(
                today.year - 1, 12, 31)))

    def test_set_get_date_range(self):
        """Test set and get date range methods."""
        self.form.set_date_range('Feb', '2014', 'Nov', '2017')
        date_range = self.form.get_date_range()
        self.assertEqual(date_range, (date(2014, 2, 1), date(2017, 11, 30)))

    def test_select_all_platforms(self) -> None:
        """Test the Select All Platforms checkbox."""
        # Toggle the 'Select all platforms' checkbox
        self.form.check_box_select_all.setChecked(True)

        # Test that all platform check boxes are checked
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertTrue(check_box.isChecked())

    def test_select_all_platforms_twice(self) -> None:
        """Test the Select All Platforms checkbox."""
        # Toggle the 'Select all platforms' checkbox
        self.form.check_box_select_all.setChecked(True)

        # Untoggle the 'Select all platforms' checkbox again
        self.form.check_box_select_all.setChecked(False)

        # Test that all platform check boxes are unchecked again
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertFalse(check_box.isChecked())

    def test_no_platform_selected(self) -> None:
        """Test clicking start without any selected platform."""
        QTimer.singleShot(100, functools.partial(
            utils.accept_qmessagebox, self))
        QTimer.singleShot(
            500, functools.partial(utils.window_visible, self, ProgressWindow))
        QTimer.singleShot(
            700, functools.partial(
                utils.cancel_window, self, ProgressWindow, 'push_button_abort'))
        self.form.push_button_start.click()

        # Check that QMessageBox was opened and ProgressWindow was not
        expected_results = [utils.QMSG_BOX_OPEN]
        self.assertEqual(self.test_results, expected_results)

    def test_output_file_on_date_change(self) -> None:
        """Test output file name after a date change."""
        old_output_file = self.form.line_edit_output_file.text()

        # Change start and/or end date
        self.form.set_date_range('Feb', '2017', 'Sep', '2017')
        self.form.on_combo_box_start_month_activated()

        new_output_file = self.form.line_edit_output_file.text()
        self.assertNotEqual(new_output_file, old_output_file)
        self.assertEqual(new_output_file, os.path.join(
            Path.home(), 'P2P_Ergebnisse_01022017-30092017.xlsx'))

    def test_output_file_on_date_change_after_user_change(self) -> None:
        """Test output file after date change if user already changed file."""
        QLineEdit.setText(self.form.line_edit_output_file, 'Test.xlsx')
        self.form.output_file_changed = True

        # Change start and/or end date
        self.form.set_date_range('Feb', '2017', 'Sep', '2017')
        self.form.on_combo_box_start_month_activated()

        # Check that the output file name was not changed
        self.assertEqual(self.form.line_edit_output_file.text(), 'Test.xlsx')

    def test_end_date_before_start_date(self) -> None:
        """Test clicking start with end date set before start date."""
        self.form.set_date_range('Feb', '2017', 'Sep', '2016')
        QTimer.singleShot(100, functools.partial(
            utils.accept_qmessagebox, self))
        QTimer.singleShot(
            500, functools.partial(utils.window_visible, self, ProgressWindow))
        QTimer.singleShot(
            700, functools.partial(
                utils.cancel_window, self, ProgressWindow, 'push_button_abort'))
        self.form.push_button_start.click()

        # Check that QMessageBox was opened and ProgressWindow was not
        expected_results = [utils.QMSG_BOX_OPEN]
        self.assertEqual(self.test_results, expected_results)

    def test_push_start_button_with_bondora_selected(self) -> None:
        """Test pushing start button after selecting Bondora."""
        # Create mock methods to avoid real calls to the Bondora website
        Bondora.download_statement = MagicMock()
        Bondora.parse_statement = MagicMock()
        self.form.check_box_bondora.setChecked(True)
        self.form.set_date_range('Sep', '2018', 'Feb', '2019')
        QLineEdit.setText(self.form.line_edit_output_file, 'Test_Bondora.xlsx')
        QTimer.singleShot(
            100, functools.partial(utils.window_visible, self, ProgressWindow))
        QTimer.singleShot(
            200, functools.partial(
                utils.cancel_window, self, ProgressWindow, 'push_button_abort'))
        QTest.mouseClick(self.form.push_button_start, Qt.LeftButton)

        # Check that ProgressWindow opened
        expected_results = [
            utils.PROG_WINDOW_VISIBLE, utils.PROG_WINDOW_CANCELLED]
        self.assertEqual(self.test_results, expected_results)

        # Check that all settings are correct
        self.assertEqual(self.form.settings.platforms, {'Bondora'})
        self.assertEqual(
            self.form.settings.date_range,
            (date(2018, 9, 1), date(2019, 2, 28)))
        self.assertEqual(self.form.settings.output_file, 'Test_Bondora.xlsx')

        # Assert that Bondora was called
        Bondora.download_statement.assert_called_once_with(
            unittest.mock.ANY, unittest.mock.ANY)

    def test_push_tool_button_settings(self) -> None:
        """Test pushing settings button."""
        QTimer.singleShot(
            500, functools.partial(utils.window_visible, self, SettingsWindow))
        QTimer.singleShot(
            700, functools.partial(
                utils.cancel_window, self, SettingsWindow))
        QTest.mouseClick(self.form.tool_button_settings, Qt.LeftButton)

        # Check that SettingsWindow opened
        expected_results = [
            utils.SETTINGS_VISIBLE, utils.SETTINGS_CANCELLED]
        self.assertEqual(self.test_results, expected_results)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(MainWindowTests)
    result = runner.run(suite)
