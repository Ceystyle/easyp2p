# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the settings window of easyp2p."""

import functools
import sys
import unittest

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QDialogButtonBox
from PyQt5.QtTest import QTest

import easyp2p.p2p_credentials as p2p_cred
from easyp2p.p2p_settings import Settings
from easyp2p.ui.settings_window import SettingsWindow
import tests.utils as utils
from tests.test_credentials import fill_credentials_window

app = QApplication(sys.argv)


class SettingsWindowTests(unittest.TestCase):
    """Test the settings window of easyp2p."""

    def setUp(self) -> None:
        """Initialize SettingsWindow."""
        self.settings = Settings()
        self.platforms = {'TestPlatform1', 'TestPlatform2', 'TestPlatform3'}
        self.form = SettingsWindow(self.platforms, self.settings)
        self.test_results = []

    def tearDown(self) -> None:
        """Remove all test platforms from keyring."""
        for platform in self.platforms:
            try:
                p2p_cred.delete_platform_from_keyring(platform)
            except RuntimeError:
                pass

    @unittest.skipIf(not p2p_cred.keyring_exists(), "No keyring available!")
    def test_defaults_with_keyring(self):
        """Test default behaviour if keyring is available."""
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.assertEqual(0, self.form.list_widget_platforms.count())
        self.assertEqual(set(), self.form.saved_platforms)
        self.assertTrue(self.form.push_button_add.isEnabled())
        self.assertTrue(self.form.push_button_change.isEnabled())
        self.assertTrue(self.form.push_button_delete.isEnabled())

    @unittest.skipIf(p2p_cred.keyring_exists(), "Keyring is available!")
    def test_defaults_without_keyring(self):
        """Test default behaviour if keyring is not available."""
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.assertEqual(1, self.form.list_widget_platforms.count())
        self.assertEqual(
            'Kein Keyring vorhanden!',
            self.form.list_widget_platforms.item(0).text())
        self.assertFalse(self.form.push_button_add.isEnabled())
        self.assertFalse(self.form.push_button_change.isEnabled())
        self.assertFalse(self.form.push_button_delete.isEnabled())

    def test_push_button_add(self):
        """Test adding a platform to the keyring."""
        QTimer.singleShot(200, functools.partial(
            utils.accept_qinputdialog, self))
        QTimer.singleShot(
            500, functools.partial(
                fill_credentials_window, 'foo', 'bar', True))
        QTest.mouseClick(self.form.push_button_add, Qt.LeftButton)
        self.assertEqual(1, self.form.list_widget_platforms.count())
        self.assertEqual(
            'TestPlatform1',
            self.form.list_widget_platforms.item(0).text())

    def test_push_button_delete(self):
        """Test deleting a platform from the keyring."""
        # First add the platform and mark it
        self.test_push_button_add()
        self.form.list_widget_platforms.setCurrentRow(0)

        QTimer.singleShot(100, functools.partial(
            utils.accept_qmessagebox, self))
        QTest.mouseClick(self.form.push_button_delete, Qt.LeftButton)
        self.assertEqual(set(), self.form.saved_platforms)
        self.assertEqual(0, self.form.list_widget_platforms.count())

    def test_accept_with_headless_true(self):
        """Keep default value True for headless and click OK."""
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertTrue(self.form.settings.headless)

    def test_accept_with_headless_false(self):
        """Change headless to False and click OK. Must still be False."""
        self.form.check_box_headless.setChecked(False)
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertFalse(self.form.settings.headless)

    def test_cancel_with_headless_true(self):
        """
        Keep headless default value and click Cancel. headless must be True.
        """
        self.assertTrue(self.form.check_box_headless.isChecked())
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertTrue(self.form.settings.headless)

    def test_cancel_with_headless_false(self):
        """
        Set headless to False and click Cancel. Headless must be back to True.
        """
        self.form.check_box_headless.setChecked(False)
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertTrue(self.form.settings.headless)


if __name__ == "__main__":
    unittest.main()
