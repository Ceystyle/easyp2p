# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the main window of easyp2p."""

import calendar
from datetime import date
import functools
import os
import sys
from typing import Union
import unittest

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QLineEdit, QMessageBox)
from PyQt5.QtTest import QTest

import easyp2p.p2p_helper as p2p_helper
#from easyp2p.p2p_settings import Settings
from easyp2p.ui.credentials_window import CredentialsWindow
from easyp2p.ui.main_window import MainWindow
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.settings_window import SettingsWindow

APP = QApplication(sys.argv)
# TODO: add tests to check if Settings are correct


class MainWindowTests(unittest.TestCase):

    """Test the main window of easyp2p."""

    def setUp(self) -> None:
        """Create the GUI."""
        self.form = MainWindow()
        self.message_box_open = False
        self.progress_window_open = False
        self.window_open = False

    def test_defaults(self) -> None:
        """Test GUI in default state."""

        # All check boxes are unchecked in default state
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertFalse(check_box.isChecked())

        # Check if output file name is set correctly
        date_range = self.form.get_date_range()
        self.assertTrue(self.form.line_edit_output_file.text() == os.path.join(
            os.getcwd(), 'P2P_Ergebnisse_{0}-{1}.xlsx'.format(
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
        # Push the start button without selecting any platform first
        QTimer.singleShot(500, self.is_message_box_open)
        QTimer.singleShot(
            500, functools.partial(self.is_window_open, ProgressWindow))
        self.form.push_button_start.click()

        # Check that warning message pops up and ProgressWindow did not open
        self.assertTrue(self.message_box_open)
        self.assertFalse(self.window_open)

    def test_output_file_on_date_change(self) -> None:
        """Test output file name after a date change."""
        old_output_file = self.form.line_edit_output_file.text()

        # Change start and/or end date
        self.form.set_date_range('Feb', '2017', 'Sep', '2017')
        self.form.on_combo_box_start_month_activated()

        new_output_file = self.form.line_edit_output_file.text()
        self.assertNotEqual(new_output_file, old_output_file)
        self.assertEqual(new_output_file, os.path.join(
            os.getcwd(), 'P2P_Ergebnisse_01022017-30092017.xlsx'))

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

        # Push the start button
        QTimer.singleShot(500, self.is_message_box_open)
        QTimer.singleShot(
            500, functools.partial(self.is_window_open, ProgressWindow))
        self.form.push_button_start.click()

        # Check that warning message pops up and ProgressWindow did not open
        self.assertTrue(self.message_box_open)
        self.assertFalse(self.window_open)

    def test_push_start_button_with_bondora_selected(self) -> None:
        """Test pushing start button after selecting Bondora."""
        self.form.check_box_bondora.setChecked(True)
        self.form.set_date_range('Sep', '2018', 'Feb', '2019')
        QLineEdit.setText(self.form.line_edit_output_file, 'Test_Bondora.xlsx')
        QTimer.singleShot(
            500, functools.partial(self.is_window_open, ProgressWindow))
        QTest.mouseClick(self.form.push_button_start, Qt.LeftButton)

        # Check that the progress window opened
        self.assertTrue(self.window_open)

        # Check that all settings are correct
        self.assertEqual(self.form.settings.platforms, {'Bondora'})
        self.assertEqual(
            self.form.settings.date_range,
            (date(2018, 9, 1), date(2019, 2, 28)))
        self.assertEqual(self.form.settings.output_file, 'Test_Bondora.xlsx')

    def test_push_tool_button_settings(self) -> None:
        """Test pushing settings button."""
        QTimer.singleShot(
            500, functools.partial(self.is_window_open, SettingsWindow))
        QTest.mouseClick(self.form.tool_button_settings, Qt.LeftButton)

        # Check that the progress window opened
        self.assertTrue(self.window_open)

    def is_message_box_open(self) -> bool:
        """Helper method to determine if a QMessageBox is open."""
        all_top_level_widgets = QApplication.topLevelWidgets()
        for widget in all_top_level_widgets:
            if isinstance(widget, QMessageBox):
                QTest.keyClick(widget, Qt.Key_Enter)
                self.message_box_open = True
                return True
        self.message_box_open = False
        return False

    def is_window_open(
            self, window: Union[
                CredentialsWindow, ProgressWindow, SettingsWindow]) -> bool:
        """Helper method to determine if a window is open."""
        all_top_level_widgets = QApplication.topLevelWidgets()
        for widget in all_top_level_widgets:
            if isinstance(widget, window):
                widget.reject()
                self.window_open = True
                return True
        self.window_open = False
        return False


if __name__ == "__main__":
    unittest.main()
