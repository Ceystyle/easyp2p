# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module implementing ProgressWindow."""

import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from easyp2p.p2p_settings import Settings
from easyp2p.p2p_worker import WorkerThread
from easyp2p.ui.Ui_progress_window import Ui_ProgressWindow


class ProgressWindow(QDialog, Ui_ProgressWindow):

    """Contains code for handling events for the Progress Window."""

    abort = pyqtSignal()

    def __init__(self, settings: Settings) -> None:
        """
        Constructor of ProgressWindow class.

        Args:
            settings: Settings for easyp2p

        """
        super().__init__()
        self.setupUi(self)

        # Initialize progress bar
        # Each platform has 7 stages (init ChromeDriver, log in, open statement
        # page, generate + download statement, log out, parse statement) plus
        # one common stage for writing the results to Excel
        self.progress_bar.setMaximum(len(settings.platforms) * 7 + 1)
        self.progress_bar.setValue(0)

        # Disable the Ok button
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        # Initialize and start worker thread
        self.worker = WorkerThread(settings)
        self.worker.signals.end_easyp2p.connect(self.end_easyp2p)
        self.worker.signals.update_progress_bar.connect(
            self.update_progress_bar)
        self.worker.signals.add_progress_text.connect(
            self.add_progress_text)
        self.abort.connect(self.worker.signals.abort_signal)
        self.worker.start()

    @pyqtSlot()
    def on_button_box_rejected(self) -> None:
        """
        Abort the evaluation of the selected P2P platforms.

        If the abort button is clicked, the worker thread will finish the
        processing of the current platform and then stop. It does not abort
        immediately to ensure a clean logout of the P2P site.

        """
        self.abort.emit()
        self.reject()

    @pyqtSlot()
    def update_progress_bar(self) -> None:
        """Update the progress bar in ProgressWindow to new value."""
        if self.worker.done:
            self.progress_bar.setValue(self.progress_bar.maximum())
        else:
            self.progress_bar.setValue(self.progress_bar.value() + 1)
        if self.progress_bar.value() == self.progress_bar.maximum():
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    @pyqtSlot(str, bool)
    def add_progress_text(self, txt: str, print_red: bool) -> None:
        """
        Append a new line to the progress text in ProgressWindow.

        Args:
            txt: String to add to progress text
            print_red: If True print the message in red, if False print in
                black.

        """
        if print_red:
            color = QColor(100, 0, 0)  # red
        else:
            color = QColor(0, 0, 0)  # black
        self.progress_text.setTextColor(color)
        self.progress_text.append(txt)

    @pyqtSlot(str, str)
    def end_easyp2p(self, error_msg: str, header: str) -> None:
        """
        Abort the program in case of critical errors.

        Args:
            error_msg: Message to display to the user before aborting.
            header: Header text of the error message window.

        """
        QMessageBox.critical(self, header, error_msg, QMessageBox.Close)
        self.abort.emit()
        self.reject()
        sys.exit()
