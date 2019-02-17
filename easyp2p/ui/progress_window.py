# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing ProgressWindow."""

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog

from ui.Ui_progress_window import Ui_Dialog





class ProgressWindow(QDialog, Ui_Dialog):

    """Contains code for handling events for the Progress Window."""

    def __init__(self, parent=None):
        """
        Constructor.

        Keyword Args:
            parent (QWidget): reference to the parent widget

        """
        super(ProgressWindow, self).__init__(parent)
        self.setupUi(self)

    @pyqtSlot()
    def on_pushButton_ok_clicked(self):
        """
        Close the progress window.

        Only clickable after the progress bar reaches 100%, i.e. after all
        selected P2P platforms were evaluated.

        """
        self.accept()

    @pyqtSlot()
    def on_pushButton_abort_clicked(self):
        """
        Abort the evaluation of the selected P2P platforms.

        If the abort button is clicked, the worker thread will finish the
        processing of the current platform and then stop. It does not abort
        immediately to ensure a clean logout of the P2P site.

        """
        self.reject()

    @pyqtSlot(int)
    def on_progressBar_valueChanged(self, value):
        """
        If progress bar reaches 100% make the OK button clickable.

        Args:
            value (int): Value of the progress bar, between 0 and 100

        """
        if value == 100:
            self.pushButton_ok.setEnabled(True)
