# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the credentials window of easyp2p."""

import functools
import sys
from typing import Union
import unittest

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QDialogButtonBox,  QMessageBox)
from PyQt5.QtTest import QTest

from easyp2p.ui.credentials_window import CredentialsWindow
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.settings_window import SettingsWindow

app = QApplication(sys.argv)


class CredentialsWindowTests(unittest.TestCase):

    """Test the credentials window of easyp2p."""

    def setUp(self):
        """Initialize CredentialsWindow."""
        self.form = CredentialsWindow('test_platform')
        self.message_box_open = False
        self.window_open = False

    def test_defaults(self):
        """Test default behaviour of CredentialsWindow."""
        self.assertFalse(self.form.line_edit_username.text())
        self.assertFalse(self.form.line_edit_password.text())
        self.assertFalse(self.form.check_box_save_in_keyring.isChecked())

    def test_save_in_keyring_parameter(self):
        """Test behaviour of CredentialsWindow if save_in_keyring==True."""
        self.form = CredentialsWindow('test_platform', True)
        self.assertTrue(self.form.check_box_save_in_keyring.isChecked())
        self.assertFalse(self.form.check_box_save_in_keyring.isEnabled())

    def test_no_input(self):
        """Test clicking OK without entering credentials."""
        QTimer.singleShot(500, self.is_message_box_open)
        QTimer.singleShot(
            500, functools.partial(self.is_window_open, CredentialsWindow))
        # Check that message box opened and CredentialsWindow is still open
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertTrue(self.message_box_open)

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
