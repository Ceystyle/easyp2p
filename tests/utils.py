# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing utility functions to support the tests of easyp2p."""

import unittest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest

from easyp2p.ui.credentials_window import CredentialsWindow

QMSG_BOX_OPEN = 'QMessageBox is open!'
QMSG_BOX_NOT_OPEN = 'QMessageBox is not open!'
CRED_WINDOW_VISIBLE = '{0} is visible!'.format(CredentialsWindow)
CRED_WINDOW_NOT_VISIBLE = '{0} is not visible!'.format(CredentialsWindow)


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


def window_visible(testclass: unittest.TestCase, window) -> None:
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
    testclass.test_failures.append('{0} is not visible!'.format(window))
