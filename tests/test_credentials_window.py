# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the credentials window of easyp2p."""

import sys
import unittest.mock

from PyQt5.QtWidgets import QApplication, QDialogButtonBox, QLineEdit

from easyp2p.ui.credentials_window import CredentialsWindow

APP = QApplication(sys.argv)


class CredentialsWindowTests(unittest.TestCase):

    """Test the credentials window of easyp2p."""

    def setUp(self):
        """Initialize dialog for most of the tests."""
        self.form = CredentialsWindow('TestPlatform', True)

    def test_defaults_with_keyring(self):
        """Test default behaviour if keyring_exists==True."""
        self.assertFalse(self.form.line_edit_username.text())
        self.assertFalse(self.form.line_edit_password.text())
        self.assertEqual(
            self.form.label_platform.text(),
            'Please enter username and password for TestPlatform:')
        self.assertFalse(self.form.check_box_save_in_keyring.isChecked())

    def test_defaults_without_keyring(self):
        """Test default behaviour if keyring_exists==False."""
        self.form = CredentialsWindow('TestPlatform', False)
        self.assertFalse(self.form.line_edit_username.text())
        self.assertFalse(self.form.line_edit_password.text())
        self.assertEqual(
            self.form.label_platform.text(),
            'Please enter username and password for TestPlatform:')
        self.assertFalse(self.form.check_box_save_in_keyring.isChecked())
        self.assertFalse(self.form.check_box_save_in_keyring.isEnabled())

    def test_save_in_keyring_with_keyring(self):
        """Test if a keyring is available and save_in_keyring==True."""
        self.form = CredentialsWindow('TestPlatform', True, True)
        self.assertTrue(self.form.check_box_save_in_keyring.isChecked())
        self.assertFalse(self.form.check_box_save_in_keyring.isEnabled())

    def test_save_in_keyring_without_keyring(self):
        """Test if a keyring is not available and save_in_keyring==True."""
        self.form = CredentialsWindow('TestPlatform', False, True)
        self.assertFalse(self.form.check_box_save_in_keyring.isChecked())
        self.assertFalse(self.form.check_box_save_in_keyring.isEnabled())

    @unittest.mock.patch('easyp2p.ui.credentials_window.QMessageBox.warning')
    def test_no_input(self, mock_warning):
        """Test clicking OK without entering credentials."""
        self.form.button_box.button(self.form.button_box.Ok).click()
        # Check that a warning was emitted and the window is still open
        mock_warning.assert_called_once_with(
            self.form, 'Fields are not filled',
            'Please fill in fields for username and password!')
        self.assertFalse(self.form.result())
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)
        self.assertFalse(self.form.save_in_keyring)

    @unittest.mock.patch('easyp2p.ui.credentials_window.QMessageBox.warning')
    def test_missing_username(self, mock_warning):
        """Test clicking OK without entering username."""
        QLineEdit.setText(self.form.line_edit_password, 'TestPass')
        self.form.button_box.button(self.form.button_box.Ok).click()
        # Check that a warning was emitted and the window is still open
        mock_warning.assert_called_once_with(
            self.form, 'Fields are not filled',
            'Please fill in fields for username and password!')
        self.assertFalse(self.form.result())
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)
        self.assertFalse(self.form.save_in_keyring)

    @unittest.mock.patch('easyp2p.ui.credentials_window.QMessageBox.warning')
    def test_missing_password(self, mock_warning):
        """Test clicking OK without entering password."""
        QLineEdit.setText(self.form.line_edit_username, 'TestUser')
        self.form.button_box.button(self.form.button_box.Ok).click()
        # Check that a warning was emitted and the window is still open
        mock_warning.assert_called_once_with(
            self.form, 'Fields are not filled',
            'Please fill in fields for username and password!')
        self.assertFalse(self.form.result())
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)
        self.assertFalse(self.form.save_in_keyring)

    def test_input_credentials_save_in_keyring_true(self):
        """
        Test entering credentials and check save_in_keyring then click OK.
        """
        QLineEdit.setText(self.form.line_edit_username, 'TestUser')
        QLineEdit.setText(self.form.line_edit_password, 'TestPass')
        self.form.check_box_save_in_keyring.setChecked(True)
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertEqual(self.form.username, 'TestUser')
        self.assertEqual(self.form.password, 'TestPass')
        self.assertTrue(self.form.save_in_keyring)

    def test_input_credentials_save_in_keyring_false(self):
        """
        Test entering credentials and not check save_in_keyring then click OK.
        """
        QLineEdit.setText(self.form.line_edit_username, 'TestUser')
        QLineEdit.setText(self.form.line_edit_password, 'TestPass')
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertEqual(self.form.username, 'TestUser')
        self.assertEqual(self.form.password, 'TestPass')
        self.assertFalse(self.form.save_in_keyring)

    def test_input_credentials_cancel(self):
        """Test enter credentials, check save_in_keyring and click Cancel."""
        QLineEdit.setText(self.form.line_edit_username, 'TestUser')
        QLineEdit.setText(self.form.line_edit_password, 'TestPass')
        self.form.check_box_save_in_keyring.setChecked(True)
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)
        self.assertFalse(self.form.save_in_keyring)

    def test_cancel_save_in_keyring_true(self):
        """Test clicking Cancel when save_in_keyring==True."""
        self.form = CredentialsWindow('TestPlatform', True, True)
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)
        self.assertFalse(self.form.save_in_keyring)

    @unittest.mock.patch('easyp2p.ui.credentials_window.QMessageBox.warning')
    def test_warn_user(self, mock_warning):
        self.form.warn_user('TestWarning', 'This is a test warning!')
        mock_warning.assert_called_once_with(
            self.form, 'TestWarning', 'This is a test warning!')


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(CredentialsWindowTests)
    result = runner.run(suite)
