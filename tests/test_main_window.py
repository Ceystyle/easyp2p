# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the main window of easyp2p."""

import calendar
import os
import sys
import unittest.mock
from datetime import date
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QCheckBox, QLineEdit

from easyp2p.ui.main_window import MainWindow

APP = QApplication(sys.argv)


class MainWindowTests(unittest.TestCase):

    """Test the main window of easyp2p."""

    ALL_PLATFORMS = {
        'Bondora', 'DoFinance', 'Estateguru', 'Grupeer', 'Iuvo', 'Mintos',
        'PeerBerry', 'Robocash', 'Swaper', 'Twino'
    }

    def setUp(self) -> None:
        """Create the GUI."""
        self.form = MainWindow()

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
            self.assertEqual(
                date_range, (date(today.year, today.month - 1, 1), date(
                    today.year, today.month - 1,
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
        self.assertEqual(platforms, self.ALL_PLATFORMS)

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
        self.assertEqual(platforms, self.ALL_PLATFORMS)

    def test_get_platforms_checked_false(self) -> None:
        """Test get_platforms if checked==False."""
        platforms = self.form.get_platforms(False)
        self.assertEqual(platforms, self.ALL_PLATFORMS)

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

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    @unittest.mock.patch('easyp2p.ui.main_window.QMessageBox.warning')
    def test_no_platform_selected(self, mock_warning, mock_dialog) -> None:
        """Test clicking start without any selected platform."""
        self.form.push_button_start.click()

        # Check that QMessageBox was opened and ProgressWindow was not
        mock_warning.assert_called_once_with(
            self.form,
            'Keine P2P Plattform ausgewählt!',
            'Bitte wähle mindestens eine P2P Plattform aus!')
        self.assertFalse(mock_dialog.called)

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    @unittest.mock.patch('easyp2p.ui.main_window.QMessageBox.warning')
    def test_end_date_before_start_date(
            self, mock_warning, mock_dialog) -> None:
        """Test clicking start with end date set before start date."""
        self.form.set_date_range('Feb', '2017', 'Sep', '2016')
        self.form.push_button_start.click()

        # Check that QMessageBox was opened and ProgressWindow was not
        mock_warning.assert_called_once_with(
            self.form,
            'Startdatum liegt nach Enddatum!',
            'Das Startdatum darf nicht nach dem Enddatum liegen!')
        self.assertFalse(mock_dialog.called, 'ProgressWindow was opened!')

    @unittest.mock.patch('easyp2p.ui.main_window.ProgressWindow')
    def test_push_start_button_with_bondora_selected(self, mock_dialog) -> None:
        """Test pushing start button after selecting Bondora."""
        self.form.check_box_bondora.setChecked(True)
        self.form.set_date_range('Sep', '2018', 'Feb', '2019')
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
        self.form.set_date_range('Sep', '2018', 'Feb', '2019')
        QLineEdit.setText(self.form.line_edit_output_file, 'Test.xlsx')

        selected_platforms = set()
        for platform in self.ALL_PLATFORMS:
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


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(MainWindowTests)
    result = runner.run(suite)
