# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the progress window of easyp2p."""

from datetime import date
import functools
import os
import sys
import unittest

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from easyp2p.p2p_settings import Settings
from easyp2p.ui.progress_window import ProgressWindow
from tests.test_credentials import fill_credentials_window

APP = QApplication(sys.argv)


class ProgressWindowTests(unittest.TestCase):

    """Test the progress window of easyp2p."""

    def setUp(self):
        """Initialize ProgressWindow."""
        settings = Settings()
        settings.platforms = {'test_platform1', 'test_platform2'}
        settings.date_range = (date(2018, 9, 1), date(2018, 12, 31))
        settings.output_file = os.path.join(os.getcwd(), 'test.xlsx')
        QTimer.singleShot(100, functools.partial(
            fill_credentials_window, 'TestUser', 'TestPass', False))
        QTimer.singleShot(200, functools.partial(
            fill_credentials_window, 'TestUser', 'TestPass', False))
        self.form = ProgressWindow(settings)

    def tearDown(self):
        """Stop the worker thread after test is done."""
        self.form.worker.abort = True
        self.form.worker.quit()
        self.form.worker.wait()

    def test_defaults(self):
        """Test default behaviour of ProgressWindow."""
        self.assertEqual(self.form.progress_bar.value(), 0)
        self.assertEqual(self.form.progress_text.isReadOnly(), True)
        self.assertEqual(self.form.progress_text.toPlainText(), '')
        self.assertEqual(self.form.push_button_ok.isEnabled(), False)
        self.assertEqual(self.form.push_button_abort.isEnabled(), True)

    def test_progress_text(self):
        """Test appending a line to progress_text."""
        self.form.worker.add_progress_text.emit(
            'Test message', self.form.worker.BLACK)
        self.assertEqual(self.form.progress_text.toPlainText(), 'Test message')

    def test_progress_bar(self):
        """Test updating progress_bar to maximum value."""
        self.form.worker.update_progress_bar.emit()
        self.assertEqual(self.form.progress_bar.value(), 1)
        self.form.worker.update_progress_bar.emit()
        self.assertEqual(self.form.progress_bar.value(), 2)
        # Two is the maximum value so the ok button must be enabled
        self.assertEqual(self.form.push_button_ok.isEnabled(), True)
        # Further increasing the progress_bar should not work
        self.form.worker.update_progress_bar.emit()
        self.assertEqual(self.form.progress_bar.value(), 2)


if __name__ == "__main__":
    unittest.main()
