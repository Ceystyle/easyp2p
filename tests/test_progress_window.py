# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for the progress window of easyp2p."""

import os
import sys
import unittest.mock
from datetime import date

from PyQt5.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

from easyp2p.p2p_settings import Settings
from easyp2p.ui.progress_window import ProgressWindow

APP = QApplication(sys.argv)


class ProgressWindowTests(unittest.TestCase):

    """Test the progress window of easyp2p."""

    @unittest.mock.patch('easyp2p.ui.progress_window.get_credentials')
    @unittest.mock.patch('easyp2p.ui.progress_window.WorkerThread.start')
    def setUp(self, mock_worker, mock_credentials):
        """Initialize ProgressWindow."""
        self.settings = Settings(
            (date(2018, 9, 1), date(2018, 12, 31)),
            os.path.join(os.getcwd(), 'test.xlsx'))
        self.settings.platforms = {'test_platform1', 'test_platform2'}
        mock_credentials.return_value = 'TestUser', 'TestPass'
        credentials = {
            'test_platform1': ('TestUser', 'TestPass'),
            'test_platform2': ('TestUser', 'TestPass')}
        self.form = ProgressWindow(self.settings)
        self.assertEqual(self.form.worker.credentials, credentials)
        self.assertEqual(
            self.settings.platforms, {'test_platform1', 'test_platform2'})
        mock_worker.assert_called_once_with()

    def test_defaults(self):
        """Test default behaviour of ProgressWindow."""
        self.assertEqual(self.form.progress_bar.value(), 0)
        self.assertTrue(self.form.progress_text.isReadOnly())
        self.assertEqual(self.form.progress_text.toPlainText(), '')
        self.assertFalse(
            self.form.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertTrue(
            self.form.button_box.button(QDialogButtonBox.Cancel).isEnabled())

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
        self.assertTrue(
            self.form.button_box.button(QDialogButtonBox.Ok).isEnabled())
        # Further increasing the progress_bar should not work
        self.form.worker.update_progress_bar.emit()
        self.assertEqual(self.form.progress_bar.value(), 2)

    @unittest.mock.patch('easyp2p.ui.progress_window.sys')
    @unittest.mock.patch('easyp2p.ui.progress_window.QMessageBox.critical')
    def test_abort_easyp2p(self, mock_msg_box, mock_sys):
        """Test emitting the abort_easyp2p signal."""
        self.form.worker.abort_easyp2p.emit(
            'Test abort_easyp2p!', 'Test header')
        mock_msg_box.assert_called_once_with(
            self.form, 'Test header', 'Test abort_easyp2p!', QMessageBox.Close)
        mock_sys.exit.assert_called_once_with()

    def test_push_button_abort(self):
        """Test that the worker thread is aborted if user clicks cancel."""
        self.form.button_box.button(QDialogButtonBox.Cancel).click()
        self.assertTrue(self.form.worker.abort)
        self.assertTrue(self.form.rejected)

    def test_push_button_ok(self):
        """Test that the Ok button closes the window."""
        self.form.progress_bar.maximum()
        self.form.button_box.button(QDialogButtonBox.Ok).click()
        self.assertTrue(self.form.accepted)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(ProgressWindowTests)
    result = runner.run(suite)
