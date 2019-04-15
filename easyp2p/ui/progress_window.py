# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider
# pylint: disable=invalid-name

"""Module implementing ProgressWindow."""

from datetime import date
import sys
from typing import AbstractSet, Tuple

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QDialog, QMessageBox)

from easyp2p.p2p_worker import WorkerThread
from easyp2p.ui.Ui_progress_window import Ui_Dialog


class ProgressWindow(QDialog, Ui_Dialog):

    """Contains code for handling events for the Progress Window."""

    def __init__(
        self, platforms: AbstractSet, credentials: Tuple[str, str],
        date_range: Tuple[date, date], output_file: str, parent=None) -> None:
        """
        Constructor.

        Keyword Args:
            parent: Reference to the parent widget

        """
        super(ProgressWindow, self).__init__(parent)
        self.setupUi(self)
        self.worker = WorkerThread(
            platforms, credentials, date_range, output_file)
        self.worker.update_progress_bar.connect(
            self.update_progress_bar)
        self.worker.update_progress_text.connect(
            self.update_progress_text)
        self.worker.abort_easyp2p.connect(self.abort_easyp2p)
        self.worker.start()

    @pyqtSlot()
    def on_pushButton_ok_clicked(self) -> None:
        """
        Close the progress window.

        Only clickable after the progress bar reaches 100%, i.e. after all
        selected P2P platforms were evaluated.

        """
        self.accept()

    @pyqtSlot()
    def on_pushButton_abort_clicked(self) -> None:
        """
        Abort the evaluation of the selected P2P platforms.

        If the abort button is clicked, the worker thread will finish the
        processing of the current platform and then stop. It does not abort
        immediately to ensure a clean logout of the P2P site.

        """
        self.reject()

    @pyqtSlot(int)
    def on_progressBar_valueChanged(self, value) -> None:
        """
        If progress bar reaches 100% make the OK button clickable.

        Args:
            value: Value of the progress bar, between 0 and 100

        """
        if value == 100:
            self.pushButton_ok.setEnabled(True)

    def update_progress_bar(self, value: float) -> None:
        """
        Update the progress bar in ProgressWindow to new value.

        Args:
            value: Value of the progress bar, between 0 and 100

        """
        if not 0 <= value <= 100:
            error_message = ('Fortschrittsindikator beträgt: {0}. Er muss '
                             'zwischen 0 und 100 liegen!'.format(value))
            QMessageBox.warning(
                self, 'Fehler!', error_message)
            return

        self.progressBar.setValue(value)

    def update_progress_text(self, txt: str, color: QColor) -> None:
        """
        Append a new line to the progress text in ProgressWindow.

        Args:
            txt: String to add to progress text
            color: Color in which the message should be displayed

        """
        self.progressText.setTextColor(color)
        self.progressText.append(txt)

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
