# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing ProgressWindow."""

import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QMessageBox

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
        self.progress_bar.setMaximum(len(settings.platforms))
        self.progress_bar.setValue(0)

        # Initialize and start worker thread
        self.worker = WorkerThread(settings, credentials)
        self.worker.abort_easyp2p.connect(self.abort_easyp2p)
        self.worker.update_progress_bar.connect(
            self.update_progress_bar)
        self.worker.add_progress_text.connect(
            self.add_progress_text)
        self.worker.start()

    @pyqtSlot()
    def on_push_button_abort_clicked(self) -> None:
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
        """
        Update the progress bar in ProgressWindow to new value.

        Args:
            value: Value of the progress bar, between 0 and 100

        """
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        if self.progress_bar.value() == self.progress_bar.maximum():
            self.push_button_ok.setEnabled(True)

    def add_progress_text(self, txt: str, color: QColor) -> None:
        """
        Append a new line to the progress text in ProgressWindow.

        Args:
            txt: String to add to progress text
            color: Color in which the message should be displayed

        """
        self.progress_text.setTextColor(color)
        self.progress_text.append(txt)

    def abort_easyp2p(self, error_msg: str) -> None:
        """
        Abort the program in case of critical errors.

        Args:
            error_msg: Message to display to the user before aborting

        """
        self.reject()
        QMessageBox.critical(
            self, "Kritischer Fehler", error_msg, QMessageBox.Close)
        sys.exit()
