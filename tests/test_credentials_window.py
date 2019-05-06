# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the credentials window of easyp2p."""

import functools
import sys
import unittest

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialogButtonBox, QLineEdit

from easyp2p.ui.credentials_window import CredentialsWindow
import tests.utils as utils

APP = QApplication(sys.argv)


class CredentialsWindowTests(unittest.TestCase):

    """Test the credentials window of easyp2p."""

    def setUp(self):
        """Initialize dialog for most of the tests."""
        self.form = CredentialsWindow('TestPlatform', True)
        self.test_results = []

    def test_defaults_with_keyring(self):
        """Test default behaviour if keyring_exists==True."""
        self.assertFalse(self.form.line_edit_username.text())
        self.assertFalse(self.form.line_edit_password.text())
        self.assertFalse(self.form.check_box_save_in_keyring.isChecked())

    def test_defaults_without_keyring(self):
        """Test default behaviour if keyring_exists==False."""
        self.form = CredentialsWindow('TestPlatform', False)
        self.assertFalse(self.form.line_edit_username.text())
        self.assertFalse(self.form.line_edit_password.text())
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

    def test_no_input(self):
        """Test clicking OK without entering credentials."""
        QTimer.singleShot(
            0, self.form.button_box.button(QDialogButtonBox.Ok).click)
        QTimer.singleShot(
            400, functools.partial(utils.accept_qmessagebox, self))
        QTimer.singleShot(
            500, functools.partial(
                utils.window_visible, self, CredentialsWindow))
        QTimer.singleShot(
            600, self.form.button_box.button(QDialogButtonBox.Cancel).click)
        self.form.exec_()
        expected_results = [utils.QMSG_BOX_OPEN, utils.CRED_WINDOW_VISIBLE]
        self.assertEqual(self.test_results, expected_results)
        self.assertFalse(self.form.isVisible())

    def test_input_credentials(self):
        """Test entering credentials."""
        QLineEdit.setText(self.form.line_edit_username, 'TestUser')
        QLineEdit.setText(self.form.line_edit_password, 'TestPass')
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertEqual(self.form.username, 'TestUser')
        self.assertEqual(self.form.password, 'TestPass')

    def test_input_credentials_cancel(self):
        """Test entering credentials and then clicking Cancel."""
        QLineEdit.setText(self.form.line_edit_username, 'TestUser')
        QLineEdit.setText(self.form.line_edit_password, 'TestPass')
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)

    def test_input_credentials_cancel_with_save_in_keyring(self):
        """
        Test cancel without entering credentials and save_in_keyring checked.
        """
        self.form.check_box_save_in_keyring.setChecked(True)
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertIsNone(self.form.username)
        self.assertIsNone(self.form.password)
        self.assertFalse(self.form.save_in_keyring)


if __name__ == "__main__":
    unittest.main()
