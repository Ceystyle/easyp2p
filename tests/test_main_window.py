# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the main window of easyp2p."""

from datetime import timedelta
import os
import sys
import unittest.mock
from datetime import date
from pathlib import Path

from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QApplication, QCheckBox, QLineEdit

from easyp2p.ui.main_window import MainWindow
from tests import PLATFORMS

APP = QApplication(sys.argv)


class MainWindowTests(unittest.TestCase):

    """Test the main window of easyp2p."""

    def setUp(self) -> None:
        """Create the GUI."""
        self.form = MainWindow(APP)

    def set_date_combo_boxes(
            self, start_month: int, start_year: int, end_month: int,
            end_year: int) -> None:
        """
        Helper method to set the indices of the date combo boxes

        Args:
            start_month: Index of start month combo box entry.
            start_year: Index of start year combo box entry.
            end_month: Index of end month combo box entry.
            end_year: Index of end year combo box entry.

        """
        self.form.combo_box_start_month.setCurrentIndex(start_month)
        self.form.combo_box_start_year.setCurrentIndex(start_year)
        self.form.combo_box_end_month.setCurrentIndex(end_month)
        self.form.combo_box_end_year.setCurrentIndex(end_year)
        self.form.on_combo_box_start_year_activated()

    def test_defaults(self) -> None:
        """Test GUI in default state."""

        # All check boxes are unchecked in default state
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertFalse(check_box.isChecked())

        # Check if date_range is correct
        end_last_month = date.today().replace(day=1) - timedelta(days=1)
        date_range = (end_last_month.replace(day=1), end_last_month)
        self.assertEqual(date_range, self.form.date_range)

        # Check if date combo boxes are correct
        self.assertEqual(
            QLocale().monthName(date_range[0].month, 1),
            self.form.combo_box_start_month.currentText())
        self.assertEqual(
            str(date_range[0].year),
            self.form.combo_box_start_year.currentText())
        self.assertEqual(
            QLocale().monthName(date_range[1].month, 1),
            self.form.combo_box_end_month.currentText())
        self.assertEqual(
            str(date_range[1].year),
            self.form.combo_box_end_year.currentText())

        # Check if output file name is set correctly
        # date_range = self.form.get_date_range()
        self.assertEqual(
            self.form.line_edit_output_file.text(), os.path.join(
                str(Path.home()), 'P2P_Results_{0}-{1}.xlsx'.format(
                    date_range[0].strftime('%d%m%Y'),
                    date_range[1].strftime('%d%m%Y'))))

    def test_select_all_platforms(self) -> None:
        """Test the Select All Platforms checkbox."""
        # Toggle the 'Select all platforms' checkbox
        self.form.check_box_select_all.setChecked(True)

        # Test that all platform check boxes are checked
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertTrue(check_box.isChecked())

    def test_get_platforms_no_platform_checked_true(self) -> None:
        """Test get_platforms if no platform is selected and checked==True."""
        platforms = self.form.get_platforms(True)
        self.assertEqual(platforms, set())

    def test_get_platforms_all_platforms_checked_true(self) -> None:
        """
        Test get_platforms if all platforms are selected and checked==True.
        """
        self.form.check_box_select_all.setChecked(True)
        platforms = self.form.get_platforms(True)
        self.assertEqual(platforms, set(PLATFORMS))

    def test_get_platforms_three_platforms_selected_checked_true(self) -> None:
        """
        Test get_platforms if three platforms are selected and checked==True.
        """
        self.form.check_box_bondora.setChecked(True)
        self.form.check_box_mintos.setChecked(True)
        self.form.check_box_twino.setChecked(True)
        platforms = self.form.get_platforms(True)
        self.assertEqual(platforms, {'Bondora', 'Mintos', 'Twino'})

    def test_get_platforms_three_platforms_selected_checked_false(self) -> None:
        """
        Test get_platforms if three platforms are selected and checked==False.
        """
        self.form.check_box_bondora.setChecked(True)
        self.form.check_box_mintos.setChecked(True)
        self.form.check_box_twino.setChecked(True)
        platforms = self.form.get_platforms(False)
        self.assertEqual(platforms, set(PLATFORMS))

    def test_get_platforms_checked_false(self) -> None:
        """Test get_platforms if checked==False."""
        platforms = self.form.get_platforms(False)
        self.assertEqual(platforms, set(PLATFORMS))

    def test_select_all_platforms_twice(self) -> None:
        """Test the Select All Platforms checkbox."""
        # Toggle the 'Select all platforms' checkbox
        self.form.check_box_select_all.setChecked(True)

        # Untoggle the 'Select all platforms' checkbox again
        self.form.check_box_select_all.setChecked(False)

        # Test that all platform check boxes are unchecked again
        for check_box in self.form.group_box_platforms.findChildren(QCheckBox):
            self.assertFalse(check_box.isChecked())

    def test_output_file_on_date_change(self) -> None:
        """Test output file name after a date change."""
        old_output_file = self.form.line_edit_output_file.text()

        # Change start and end date
        self.set_date_combo_boxes(4, 0, 10, 5)

        new_output_file = self.form.line_edit_output_file.text()
        self.assertNotEqual(new_output_file, old_output_file)
        self.assertEqual(os.path.join(
                str(Path.home()), 'P2P_Results_01052010-30112015.xlsx'),
            new_output_file)

    def test_output_file_on_date_change_after_user_change(self) -> None:
        """Test output file after date change if user already changed file."""
        QLineEdit.setText(self.form.line_edit_output_file, 'Test.xlsx')
        self.form.output_file_changed = True

        # Change start and end date
        self.set_date_combo_boxes(4, 0, 10, 5)

        # Check that the output file name was not changed
        self.assertEqual(self.form.line_edit_output_file.text(), 'Test.xlsx')

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    @unittest.mock.patch('easyp2p.ui.main_window.QMessageBox.warning')
    def test_no_platform_selected(self, mock_warning, mock_dialog) -> None:
        """Test clicking start without any selected platform."""
        self.form.push_button_start.click()

        # Check that QMessageBox was opened and ProgressWindow was not
        mock_warning.assert_called_once_with(
            self.form,
            'No P2P platform selected!',
            'Please choose at least one P2P platform!')
        self.assertFalse(mock_dialog.called)

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    @unittest.mock.patch('easyp2p.ui.main_window.QMessageBox.warning')
    def test_end_date_before_start_date(
            self, mock_warning, mock_dialog) -> None:
        """Test clicking start with end date set before start date."""
        self.set_date_combo_boxes(5, 6, 11, 5)
        self.form.push_button_start.click()

        # Check that QMessageBox was opened and ProgressWindow was not
        mock_warning.assert_called_once_with(
            self.form,
            'Start date is after end date!',
            'Start date must be before end date!')
        self.assertFalse(mock_dialog.called, 'ProgressWindow was opened!')

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    def test_push_start_button_with_bondora_selected(self, mock_dialog) -> None:
        """Test pushing start button after selecting Bondora."""
        self.form.check_box_bondora.setChecked(True)
        self.set_date_combo_boxes(8, 8, 1, 9)
        QLineEdit.setText(self.form.line_edit_output_file, 'Test.xlsx')
        self.form.push_button_start.click()

        # Check that ProgressWindow opened
        mock_dialog.assert_called_once_with(self.form.settings)

        # Check that all settings are correct
        self.assertEqual(self.form.settings.platforms, {'Bondora'})
        self.assertEqual(
            self.form.settings.date_range,
            (date(2018, 9, 1), date(2019, 2, 28)))
        self.assertEqual(self.form.settings.output_file, 'Test.xlsx')

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    def test_push_start_button_with_increasing_number_of_platforms_selected(
            self, mock_dialog) -> None:
        """
        Test push start button with increasing number of selected platforms.
        """
        self.set_date_combo_boxes(8, 8, 1, 9)
        QLineEdit.setText(self.form.line_edit_output_file, 'Test.xlsx')

        selected_platforms = set()
        for platform in PLATFORMS:
            check_box = getattr(self.form, 'check_box_' + platform.lower())
            check_box.setChecked(True)
            selected_platforms.add(platform)
            self.form.push_button_start.click()

            # Check that ProgressWindow opened
            mock_dialog.assert_called_once_with(self.form.settings)
            mock_dialog.reset_mock()

            # Check that all settings are correct
            self.assertEqual(self.form.settings.platforms, selected_platforms)
            self.assertEqual(
                self.form.settings.date_range,
                (date(2018, 9, 1), date(2019, 2, 28)))
            self.assertEqual(self.form.settings.output_file, 'Test.xlsx')

    @unittest.mock.patch('easyp2p.ui.main_window.SettingsWindow')
    def test_push_tool_button_settings(self, mock_dialog) -> None:
        """Test pushing settings button."""
        self.form.tool_button_settings.click()

        # Check that SettingsWindow opened
        mock_dialog.assert_called_once_with(
            self.form.get_platforms(False), self.form.settings)

    def test_change_language_to_german(self) -> None:
        """Test changing the language to German."""
        self.form.action_german.trigger()
        all_months = {
            self.form.combo_box_start_month.itemText(i) for i in
            range(self.form.combo_box_start_month.count())}
        all_months_expected = {
            QLocale('de_de').monthName(i, 1) for i in range(1, 13)}
        self.assertEqual(self.form.groupBox_start_date.title(), 'Startdatum')
        self.assertEqual(all_months, all_months_expected)

    def test_change_language_to_german_to_english(self) -> None:
        """Test changing the language to German and then back to English."""
        self.form.action_german.trigger()
        self.form.action_english.trigger()
        all_months = {
            self.form.combo_box_start_month.itemText(i) for i in
            range(self.form.combo_box_start_month.count())}
        all_months_expected = {
            QLocale('en_US').monthName(i, 1) for i in range(1, 13)}
        self.assertEqual(self.form.groupBox_start_date.title(), 'Start date')
        self.assertEqual(all_months, all_months_expected)

    def test_change_language_to_german_after_date_update(self) -> None:
        """
        Test changing the language to German if the dates have been changed.
        """
        self.set_date_combo_boxes(4, 7, 11, 8)
        self.form.action_german.trigger()
        self.assertEqual(
            QLocale('de_de').monthName(5, 1),
            self.form.combo_box_start_month.currentText())
        self.assertEqual(
            '2017', self.form.combo_box_start_year.currentText())
        self.assertEqual(
            QLocale('de_de').monthName(12, 1),
            self.form.combo_box_end_month.currentText())
        self.assertEqual(
            '2018', self.form.combo_box_end_year.currentText())


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(MainWindowTests)
    result = runner.run(suite)
