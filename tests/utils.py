# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing utility functions to support the tests of easyp2p."""

from typing import Union
import unittest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest

from easyp2p.ui.credentials_window import CredentialsWindow
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.settings_window import SettingsWindow

QMSG_BOX_OPEN = 'QMessageBox is open!'
QMSG_BOX_NOT_OPEN = 'QMessageBox is not open!'
CRED_WINDOW_VISIBLE = '{0} is visible!'.format(CredentialsWindow)
CRED_WINDOW_NOT_VISIBLE = '{0} is not visible!'.format(CredentialsWindow)
PROG_WINDOW_VISIBLE = '{0} is visible!'.format(ProgressWindow)
PROG_WINDOW_NOT_VISIBLE = '{0} is not visible!'.format(ProgressWindow)
PROG_WINDOW_CANCELLED = '{0} was cancelled!'.format(ProgressWindow)
PROG_WINDOW_NOT_CANCELLED = '{0} was not cancelled!'.format(ProgressWindow)
SETTINGS_VISIBLE = '{0} is visible!'.format(SettingsWindow)
SETTINGS_NOT_VISIBLE = '{0} is not visible!'.format(SettingsWindow)
SETTINGS_CANCELLED = '{0} was cancelled!'.format(SettingsWindow)
SETTINGS_NOT_CANCELLED = '{0} was not cancelled!'.format(SettingsWindow)

Windows = Union[CredentialsWindow, ProgressWindow, SettingsWindow]


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
            testclass.test_results.append(QMSG_BOX_OPEN)
            return
    testclass.test_results.append(QMSG_BOX_NOT_OPEN)


def window_visible(testclass: unittest.TestCase, window: Windows) -> None:
    """
    Check if a dialog of type window is visible. Fail test if not.

    Args:
        testclass: Instance of unittest.TestCase
        window: Type of window which should be visible

    """
    all_top_level_widgets = QApplication.topLevelWidgets()
    for widget in all_top_level_widgets:
        if isinstance(widget, window):
            if widget.isVisible():
                testclass.test_results.append('{0} is visible!'.format(window))
                return
    testclass.test_results.append('{0} is not visible!'.format(window))

def cancel_window(
        testclass: unittest.TestCase, window: Windows,
        cancel_button: str = None) -> None:
    """
    Cancel a dialog window of type window.

    Args:
        testclass: Instance of unittest.TestCase
        window: Type of window which should be cancelled
        cancel_button: Attribute name of the cancel button.
            Default is None.

    """
    all_top_level_widgets = QApplication.topLevelWidgets()
    for widget in all_top_level_widgets:
        if isinstance(widget, window):
            if cancel_button:
                button = getattr(widget, cancel_button)
                try:
                    button.click()
                except AttributeError:
                    widget.reject()
            else:
                widget.reject()
            testclass.test_results.append('{0} was cancelled!'.format(window))
            return
    testclass.test_results.append('{0} was not cancelled!'.format(window))
