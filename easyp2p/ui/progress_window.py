# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing ProgressWindow."""

import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_settings import Settings
from easyp2p.p2p_worker import WorkerThread
from easyp2p.ui.Ui_progress_window import Ui_ProgressWindow


class ProgressWindow(QDialog, Ui_ProgressWindow):

    """Contains code for handling events for the Progress Window."""

    def __init__(self, settings: Settings) -> None:
        """
        Constructor of ProgressWindow class.

        Args:
            settings: Settings for easyp2p

        """
        super().__init__()
        self.setupUi(self)

        # Get credentials for the selected platforms
        credentials = {}
        for platform in settings.platforms:
            credentials[platform] = get_credentials(platform)

        # Initialize progress bar
        # Each platform has 6 stages (log in, open statement page,
        # generate statement, download statement, log out, parse statement)
        # plus one common stage for writing the results to Excel
        self.progress_bar.setMaximum(len(settings.platforms) * 6 + 1)
        self.progress_bar.setValue(0)

        # Disable the Ok button
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        # Initialize and start worker thread
        self.worker = WorkerThread(settings, credentials)
        self.worker.abort_easyp2p.connect(self.abort_easyp2p)
        self.worker.signals.update_progress_bar.connect(
            self.update_progress_bar)
        self.worker.signals.add_progress_text.connect(
            self.add_progress_text)
        self.worker.start()

    @pyqtSlot()
    def on_button_box_rejected(self) -> None:
        """
        Abort the evaluation of the selected P2P platforms.

        If the abort button is clicked, the worker thread will finish the
        processing of the current platform and then stop. It does not abort
        immediately to ensure a clean logout of the P2P site.

        """
        self.worker.abort = True
        self.reject()
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()

    def update_progress_bar(self) -> None:
        """Update the progress bar in ProgressWindow to new value."""
        if self.worker.done:
            self.progress_bar.setValue(self.progress_bar.maximum())
        else:
            self.progress_bar.setValue(self.progress_bar.value() + 1)
        if self.progress_bar.value() == self.progress_bar.maximum():
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    def add_progress_text(self, txt: str, color: QColor) -> None:
        """
        Append a new line to the progress text in ProgressWindow.

        Args:
            txt: String to add to progress text
            color: Color in which the message should be displayed

        """
        self.progress_text.setTextColor(color)
        self.progress_text.append(txt)

    def abort_easyp2p(self, error_msg: str, header: str) -> None:
        """
        Abort the program in case of critical errors.

        Args:
            error_msg: Message to display to the user before aborting.
            header: Header text of the error message window.

        """
        self.reject()
        QMessageBox.critical(self, header, error_msg, QMessageBox.Close)
        sys.exit()
