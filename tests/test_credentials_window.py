# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the credentials window of easyp2p."""

import functools
import sys
import unittest

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QDialogButtonBox, QLineEdit, QMessageBox)
from PyQt5.QtTest import QTest

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
        self.form.setVisible(True)
        self.assertTrue(self.form.isVisible())
        # Make sure a QMessageBox appears if no credentials are provided
        QTimer.singleShot(100, functools.partial(accept_qmessagebox, self))
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        # Credentials window must still be visible
        self.assertTrue(self.form.isVisible())
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
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

def accept_qmessagebox(testclass: unittest.TestCase) -> None:
    """
    Check if a QMessageBox is open. If yes accept it. If no fail the test.

    Args:
        testclass: Instance of unittest.TestCase

    """
    all_top_level_widgets = QApplication.topLevelWidgets()
    for widget in all_top_level_widgets:
        if isinstance(widget, QMessageBox):
            QTest.keyClick(widget, Qt.Key_Enter)
            return
    testclass.fail('QMessageBox did not open!')


if __name__ == "__main__":
    unittest.main()
