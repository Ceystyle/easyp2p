# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the settings window of easyp2p."""

from datetime import date
import os
import sys
import unittest.mock

from PyQt5.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

from easyp2p.p2p_settings import Settings
from easyp2p.ui.settings_window import SettingsWindow

app = QApplication(sys.argv)

@unittest.mock.patch('easyp2p.ui.settings_window.p2p_cred')
class SettingsWindowTests(unittest.TestCase):
    """Test the settings window of easyp2p."""

    @unittest.mock.patch('easyp2p.ui.settings_window.p2p_cred')
    def setUp(self, mock_cred) -> None:
        """Initialize common parameters."""
        self.settings = Settings(
            (date(2018, 9, 1), date(2018, 12, 31)),
            os.path.join(os.getcwd(), 'test.xlsx'))
        self.platforms = ['TestPlatform1', 'TestPlatform2', 'TestPlatform3']

    def test_no_keyring(self, mock_cred):
        """Test when keyring is not available."""
        mock_cred.keyring_exists.return_value = False
        self.form = SettingsWindow(self.platforms, self.settings)
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.assertEqual(1, self.form.list_widget_platforms.count())
        self.assertEqual(
            'Kein Keyring vorhanden!',
            self.form.list_widget_platforms.item(0).text())
        self.assertFalse(self.form.push_button_add.isEnabled())
        self.assertFalse(self.form.push_button_change.isEnabled())
        self.assertFalse(self.form.push_button_delete.isEnabled())

    def test_keyring_no_platforms(self, mock_cred):
        """Test when no platforms are saved in keyring."""
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.assertEqual(0, self.form.list_widget_platforms.count())
        self.assertEqual(set(), self.form.saved_platforms)
        self.assertTrue(self.form.push_button_add.isEnabled())
        self.assertTrue(self.form.push_button_change.isEnabled())
        self.assertTrue(self.form.push_button_delete.isEnabled())

    def test_keyring_one_platform(self, mock_cred):
        """Test when one platform is saved in keyring."""
        mock_cred.get_password_from_keyring.side_effect = [
            None, 'TestUser', None]
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.assertEqual(1, self.form.list_widget_platforms.count())
        self.assertEqual({'TestPlatform2'}, self.form.saved_platforms)
        self.assertTrue(self.form.push_button_add.isEnabled())
        self.assertTrue(self.form.push_button_change.isEnabled())
        self.assertTrue(self.form.push_button_delete.isEnabled())

    def test_keyring_all_platforms(self, mock_cred):
        """Test when all platforms are saved in keyring."""
        mock_cred.get_password_from_keyring.side_effect \
            = ['TestUser'] * len(self.platforms)
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.assertEqual(
            len(self.platforms), self.form.list_widget_platforms.count())
        self.assertEqual(set(self.platforms), self.form.saved_platforms)
        self.assertTrue(self.form.push_button_add.isEnabled())
        self.assertTrue(self.form.push_button_change.isEnabled())
        self.assertTrue(self.form.push_button_delete.isEnabled())

    @unittest.mock.patch('easyp2p.ui.settings_window.QInputDialog.getItem')
    def test_push_button_add(self, mock_input, mock_cred):
        """Test adding a platform to the keyring."""
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        mock_cred.get_credentials_from_user.return_value = (
            'TestUser', 'TestPass')
        mock_input.return_value = 'TestPlatform1', True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.push_button_add.click()
        self.assertEqual(1, self.form.list_widget_platforms.count())
        self.assertEqual(
            'TestPlatform1',
            self.form.list_widget_platforms.item(0).text())
        self.assertEqual(self.form.saved_platforms, {'TestPlatform1'})

    @unittest.mock.patch('easyp2p.ui.settings_window.QInputDialog.getItem')
    def test_push_button_add_user_cancels_dialog(self, mock_input, mock_cred):
        """Test adding a platform to the keyring and user cancels dialog."""
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        mock_input.return_value = '', False
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.push_button_add.click()
        self.assertEqual(0, self.form.list_widget_platforms.count())
        self.assertEqual(self.form.saved_platforms, set())

    @unittest.mock.patch('easyp2p.ui.settings_window.QInputDialog.getItem')
    def test_push_button_add_no_credentials(self, mock_input, mock_cred):
        """
        Test adding a platform to the keyring when user enters no credentials.
        """
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        mock_cred.get_credentials_from_user.return_value = (None, None)
        mock_input.return_value = 'TestPlatform1', True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.push_button_add.click()
        self.assertEqual(0, self.form.list_widget_platforms.count())
        self.assertEqual(self.form.saved_platforms, set())

    @unittest.mock.patch('easyp2p.ui.settings_window.QMessageBox.information')
    def test_push_button_all_platforms_exist(self, mock_info, mock_cred):
        """
        Test adding platform to the keyring if all platforms are already saved.
        """
        mock_cred.get_password_from_keyring.side_effect \
            = ['TestUser'] * len(self.platforms)
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.push_button_add.click()
        mock_info.assert_called_once_with(
            self.form, 'Keine weiteren Plattformen verfügbar!',
            ('Es sind bereits Zugangsdaten für alle unterstützten '
             'Plattformen vorhanden!'))
        self.assertEqual(
            len(self.platforms), self.form.list_widget_platforms.count())
        self.assertEqual(self.form.saved_platforms, set(self.platforms))

    def test_push_button_change(self, mock_cred):
        """Test change button."""
        # Add all platforms and mark the first one
        mock_cred.get_password_from_keyring.side_effect \
            = ['TestUser'] * len(self.platforms)
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.list_widget_platforms.setCurrentRow(0)
        self.form.push_button_change.click()
        mock_cred.get_credentials_from_user.assert_called_once_with(
            'TestPlatform1', True)

    @unittest.mock.patch('easyp2p.ui.settings_window.QMessageBox.question')
    def test_push_button_delete_one_platform(self, mock_question, mock_cred):
        """Test delete button if one platform is saved."""
        # First add one platform and mark it
        mock_cred.get_password_from_keyring.side_effect = [
            None, 'TestUser', None]
        mock_cred.keyring_exists.return_value = True
        mock_question.return_value = QMessageBox.Yes
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.list_widget_platforms.setCurrentRow(0)
        self.form.push_button_delete.click()
        mock_question.assert_called_once_with(
            self.form, 'Zugangsdaten löschen?',
            'Zugangsdaten für TestPlatform2 wirklich löschen?')
        mock_cred.delete_platform_from_keyring.assert_called_once_with(
            'TestPlatform2')
        self.assertEqual(set(), self.form.saved_platforms)
        self.assertEqual(0, self.form.list_widget_platforms.count())

    @unittest.mock.patch('easyp2p.ui.settings_window.QMessageBox.question')
    def test_push_button_delete_all_platforms(self, mock_question, mock_cred):
        """Test delete button if all platforms are saved."""
        # First add one platform and mark it
        mock_cred.get_password_from_keyring.side_effect \
            = ['TestUser'] * len(self.platforms)
        mock_cred.keyring_exists.return_value = True
        mock_question.return_value = QMessageBox.Yes
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.list_widget_platforms.setCurrentRow(1)
        self.form.push_button_delete.click()
        mock_question.assert_called_once_with(
            self.form, 'Zugangsdaten löschen?',
            'Zugangsdaten für TestPlatform2 wirklich löschen?')
        mock_cred.delete_platform_from_keyring.assert_called_once_with(
            'TestPlatform2')
        self.assertEqual(
            {'TestPlatform1', 'TestPlatform3'}, self.form.saved_platforms)
        self.assertEqual(2, self.form.list_widget_platforms.count())

    def test_accept_with_headless_true(self, mock_cred):
        """Keep default value True for headless and click OK."""
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertTrue(self.form.settings.headless)

    def test_accept_with_headless_false(self, mock_cred):
        """Change headless to False and click OK. Must still be False."""
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.check_box_headless.setChecked(False)
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertFalse(self.form.settings.headless)

    def test_cancel_with_headless_true(self, mock_cred):
        """
        Keep headless default value and click Cancel. headless must be True.
        """
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertTrue(self.form.settings.headless)

    def test_cancel_with_headless_false(self, mock_cred):
        """
        Set headless to False and click Cancel. Headless must be back to True.
        """
        mock_cred.get_password_from_keyring.return_value = None
        mock_cred.keyring_exists.return_value = True
        self.form = SettingsWindow(self.platforms, self.settings)
        self.form.check_box_headless.setChecked(False)
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertTrue(self.form.settings.headless)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(SettingsWindowTests)
    result = runner.run(suite)
