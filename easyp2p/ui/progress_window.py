# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing ProgressWindow."""

from datetime import date
import sys
from typing import AbstractSet, Mapping, Optional, Tuple

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QMessageBox

from easyp2p.p2p_worker import WorkerThread
from easyp2p.ui.Ui_progress_window import Ui_ProgressWindow


class ProgressWindow(QDialog, Ui_ProgressWindow):

    """Contains code for handling events for the Progress Window."""

    def __init__(
            self, platforms: AbstractSet,
            credentials: Mapping[str, Optional[Tuple[str, str]]],
            date_range: Tuple[date, date], output_file: str) -> None:
        """
        Constructor of ProgressWindow class.

        Args:
            platforms: Set containing the names of all selected P2P
                platforms
            credentials: Dictionary containing tuples (username, password) for
                each selected P2P platform
            date_range: Date range (start_date, end_date) for which the
                account statements must be generated
            output_file: Name of the Excel file (including absolute path)
                to which the results will be written

        """
        super().__init__()
        self.setupUi(self)

        # Initialize progress bar
        self.progress_bar.setMaximum(len(platforms))
        self.progress_bar.setValue(0)

        # Initialize and start worker thread
        self.worker = WorkerThread(
            platforms, credentials, date_range, output_file)
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
