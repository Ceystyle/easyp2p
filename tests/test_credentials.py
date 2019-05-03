# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for p2p_credentials."""

import functools
import sys
import unittest
import warnings

import keyring
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialogButtonBox

from easyp2p.p2p_credentials import (
    keyring_exists, get_credentials, get_credentials_from_user,
    get_password_from_keyring, delete_platform_from_keyring,
    save_platform_in_keyring)
from easyp2p.ui.credentials_window import CredentialsWindow

APP = QApplication(sys.argv)


class CredentialsTests(unittest.TestCase):

    """Test p2p_credentials."""

    def setUp(self):
        """Ignore unnecessary ResourceWarnings for all tests."""
        warnings.simplefilter("ignore", ResourceWarning)

    @unittest.skipIf(not keyring.get_keyring(), "No keyring available!")
    def test_keyring_exists_with_keyring(self):
        """Test keyring_exists when a keyring is available."""
        self.assertTrue(keyring_exists())

    @unittest.skipIf(keyring.get_keyring(), "Keyring is available!")
    def test_keyring_exists_without_keyring(self):
        """Test keyring_exists when a keyring is not available."""
        self.assertFalse(keyring_exists())

    @unittest.skipIf(not keyring.get_keyring(), "No keyring available!")
    def test_save_platform_in_keyring(self):
        """Test save_platform_in_keyring."""
        self.assertTrue(save_platform_in_keyring(
            'TestPlatform', 'TestUser', 'TestPass'))
        self.assertEqual(
            get_password_from_keyring('TestPlatform', 'username'), 'TestUser')
        self.assertEqual(
            get_password_from_keyring('TestPlatform', 'TestUser'),
            'TestPass')

    @unittest.skipIf(not keyring.get_keyring(), "No keyring available!")
    def test_delete_platform_from_keyring_if_exists(self):
        """Test delete_platform_from_keyring if platform exists in keyring."""
        save_platform_in_keyring('TestPlatform', 'TestUser', 'TestPass')
        self.assertTrue(delete_platform_from_keyring('TestPlatform'))
        self.assertIsNone(keyring.get_password('TestPlatform', 'username'))
        self.assertIsNone(keyring.get_password('TestPlatform', 'TestUser'))

    @unittest.skipIf(not keyring.get_keyring(), "No keyring available!")
    def test_delete_platform_from_keyring_if_not_exists(self):
        """
        Test delete_platform_from_keyring if platform does not exist in keyring.
        """
        self.assertRaises(
            RuntimeError, delete_platform_from_keyring, 'TestPlatform')

    def test_get_credentials_from_user_no_save_in_keyring(self):
        """Test getting credentials from the user without saving in keyring."""
        QTimer.singleShot(100, functools.partial(
            fill_credentials_window, 'TestUser', 'TestPass', False))
        (username, password) = get_credentials_from_user('TestPlatform', True)
        self.assertEqual(username, 'TestUser')
        self.assertEqual(password, 'TestPass')

    @unittest.skipIf(not keyring.get_keyring(), "No keyring available!")
    def test_get_credentials_from_user_save_in_keyring(self):
        """Test getting credentials from the user with save in keyring."""
        QTimer.singleShot(100, functools.partial(
            fill_credentials_window, 'TestUser', 'TestPass', True))
        (username, password) = get_credentials_from_user('TestPlatform', True)
        self.assertEqual(username, 'TestUser')
        self.assertEqual(password, 'TestPass')
        self.assertEqual(
            get_password_from_keyring('TestPlatform', 'username'), 'TestUser')
        self.assertEqual(
            get_password_from_keyring('TestPlatform', 'TestUser'), 'TestPass')

    @unittest.skipIf(not keyring.get_keyring(), "No keyring available!")
    def test_get_credentials_if_in_keyring(self):
        """Get credentials which exist in the keyring."""
        save_platform_in_keyring(
            'TestPlatform', 'TestUser', 'TestPass')
        credentials = get_credentials('TestPlatform')
        self.assertEqual(credentials[0], 'TestUser')
        self.assertEqual(credentials[1], 'TestPass')

    def test_get_credentials_if_not_in_keyring(self):
        """Get credentials which do not exist in the keyring."""
        # Make sure the credentials really do not exist
        if keyring.get_keyring():
            try:
                delete_platform_from_keyring('TestPlatform')
            except RuntimeError:
                pass
        QTimer.singleShot(100, functools.partial(
            fill_credentials_window, 'TestUser', 'TestPass', False))
        credentials = get_credentials('TestPlatform')
        self.assertEqual(credentials[0], 'TestUser')
        self.assertEqual(credentials[1], 'TestPass')

    def test_get_credentials_if_not_in_keyring_cancel(self):
        """Get credentials which are not in keyring and user cancels."""
        # Make sure the credentials really do not exist
        if keyring.get_keyring():
            try:
                delete_platform_from_keyring('TestPlatform')
            except RuntimeError:
                pass
        QTimer.singleShot(100, functools.partial(
            fill_credentials_window, None, None, False))
        credentials = get_credentials('TestPlatform')
        self.assertIsNone(credentials)


def fill_credentials_window(
        username: str, password: str, save_in_keyring: bool) -> None:
    """
    Set credentials in CredentialsWindow and close the window.

    Args:
        username: Username to enter in CredentialsWindow
        password: Password to enter in CredentialsWindow
        save_in_keyring: Save credentials in keyring or not

    """
    all_top_level_widgets = QApplication.topLevelWidgets()
    for widget in all_top_level_widgets:
        if isinstance(widget, CredentialsWindow):
            widget.username = username
            widget.password = password
            widget.save_in_keyring = save_in_keyring
            widget.button_box.button(QDialogButtonBox.Cancel).click()
            return


if __name__ == "__main__":
    unittest.main()
