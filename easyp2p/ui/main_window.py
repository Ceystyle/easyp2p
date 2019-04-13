# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider
# pylint: disable=invalid-name

"""Module implementing MainWindow, the main window of easyp2p."""

import calendar
from datetime import date
import os
import sys
from typing import Sequence, Set, Tuple

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QLineEdit, QCheckBox
from PyQt5.QtWidgets import QMessageBox

import easyp2p.p2p_helper as p2p_helper
from easyp2p.p2p_worker import WorkerThread
from easyp2p.ui.credentials_window import get_credentials
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.Ui_main_window import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    """This class defines the main window of easyp2p."""

    def __init__(self, parent=None) -> None:
        """
        Constructor of MainWindow.

        Keyword Args:
            parent: Reference to the parent widget

        """
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.progress_window = None
        self.worker = None
        self.credentials = dict()
        self.init_date_combo_boxes()
        self.output_file_changed = False
        self.set_output_file()

    def init_date_combo_boxes(self) -> None:
        """Initialize date combo boxes with previous month."""
        if date.today().month > 1:
            start_month = p2p_helper.nbr_to_short_month(
                str(date.today().month - 1))
            start_year = str(date.today().year)
        else:
            start_month = 'Dez'
            start_year = str(date.today().year - 1)

        self.comboBox_start_month.setCurrentIndex(
            self.comboBox_start_month.findText(start_month))
        self.comboBox_start_year.setCurrentIndex(
            self.comboBox_start_year.findText(start_year))
        self.comboBox_end_month.setCurrentIndex(
            self.comboBox_end_month.findText(start_month))
        self.comboBox_end_year.setCurrentIndex(
            self.comboBox_end_year.findText(start_year))

    def get_date_range(self) -> Tuple[date, date]:
        """
        Get currently selected date range from combo boxes.

        Returns:
            Date range (start_date, end_date)

        """
        start_month = int(p2p_helper.short_month_to_nbr(
            str(self.comboBox_start_month.currentText())))
        start_year = int(self.comboBox_start_year.currentText())
        end_month = int(p2p_helper.short_month_to_nbr(
            str(self.comboBox_end_month.currentText())))
        end_year = int(self.comboBox_end_year.currentText())
        last_day_of_month = calendar.monthrange(end_year, end_month)[1]
        return (date(start_year, start_month, 1),
                date(end_year, end_month, last_day_of_month))

    def get_platforms(self) -> Set[str]:
        """
        Get list of all platforms selected by the user.

        Returns:
            Set of P2P platforms

        """
        platforms = set()
        for check_box in self.groupBox_platforms.findChildren(QCheckBox):
            if check_box.isChecked():
                platforms.add(check_box.text().replace('&', ''))
        return platforms

    def set_output_file(self) -> None:
        """Helper method to set the name of the output file."""
        date_range = self.get_date_range()
        if not self.output_file_changed:
            output_file = os.path.join(
                os.getcwd(), 'P2P_Ergebnisse_{0}-{1}.xlsx'.format(
                    date_range[0].strftime('%d.%m.%Y'),
                    date_range[1].strftime('%d.%m.%Y')))
            QLineEdit.setText(self.lineEdit_output_file, output_file)

    @pyqtSlot(str)
    def on_comboBox_start_month_activated(self) -> None:
        """Update output file if user changed start month in the combo box."""
        self.set_output_file()

    @pyqtSlot(str)
    def on_comboBox_start_year_activated(self) -> None:
        """Update output file if user changed start year in the combo box."""
        self.set_output_file()

    @pyqtSlot(str)
    def on_comboBox_end_month_activated(self) -> None:
        """Update output file if user changed end month in the combo box."""
        self.set_output_file()

    @pyqtSlot(str)
    def on_comboBox_end_year_activated(self, year: str) -> None:
        """Update output file if user changed end year in the combo box."""
        self.set_output_file()

    @pyqtSlot()
    def on_pushButton_file_chooser_clicked(self) -> None:
        """
        Open dialog window for changing the save location of the results file.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Ausgabedatei wählen", self.lineEdit_output_file.text(),
            "MS Excel Dateien (*.xlsx)", options=options)
        if output_file:
            # The file name must include xlsx file format. Otherwise the Excel
            # writer will crash later.
            if not output_file.endswith('.xlsx'):
                output_file += '.xlsx'
            QLineEdit.setText(self.lineEdit_output_file, output_file)
            self.output_file_changed = True

    @pyqtSlot(bool)
    def on_checkBox_select_all_toggled(self, checked: bool) -> None:
        """
        Toggle/untoggle all P2P platforms.

        Args:
            checked: if True toggle all check boxes, if False untoggle
                all check boxes

        """
        for check_box in self.groupBox_platforms.findChildren(QCheckBox):
            check_box.setChecked(checked)

    @pyqtSlot()
    def on_pushButton_start_clicked(self) -> None:
        """
        Start evaluation for selected P2P platforms and the given date range.

        The evaluation will be done by a worker thread in class WorkerThread.
        Progress is tracked in ProgressWindow.

        """
        date_range = self.get_date_range()
        platforms = self.get_platforms()

        # Check that start date is before end date
        if date_range[0] > date_range[1]:
            QMessageBox.warning(
                self, 'Startdatum liegt nach Enddatum!',
                'Das Startdatum darf nicht nach dem Enddatum liegen!')
            return

        # Check that at least one platform is selected
        if not platforms:
            QMessageBox.warning(
                self, 'Keine P2P Plattform ausgewählt!',
                'Bitte wähle mindestens eine P2P Plattform aus')
            return

        # Get credentials from user/keyring for all selected platforms
        for platform in platforms:
            self.credentials[platform] = get_credentials(platform)

        # Set up and start worker thread
        worker = self.setup_worker_thread(platforms, date_range)
        worker.start()

        # Open progress window
        self.progress_window = ProgressWindow()
        self.progress_window.exec_()

        # Abort the worker thread if user clicked the cancel button
        if self.progress_window.result() == 0:
            worker.abort = True

    def setup_worker_thread(
            self, platforms: Sequence[str], date_range: Tuple[date, date]) \
            -> 'WorkerThread':
        """
        Setup the worker thread and its attributes.

        Args:
            platforms: List of P2P platforms to evaluate
            date_range: Date range for account statement generation

        Returns:
            Handle of the worker thread

        """
        worker = WorkerThread(
            platforms, self.credentials, date_range,
            self.lineEdit_output_file.text())
        worker.update_progress_bar.connect(self.update_progress_bar)
        worker.update_progress_text.connect(self.update_progress_text)
        worker.abort_easyp2p.connect(self.abort_easyp2p)
        return worker

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

        self.progress_window.progressBar.setValue(value)

    def update_progress_text(self, txt: str, color: QColor) -> None:
        """
        Append a new line to the progress text in ProgressWindow.

        Args:
            txt: String to add to progress text
            color: Color in which the message should be displayed

        """
        self.progress_window.progressText.setTextColor(color)
        self.progress_window.progressText.append(txt)

    def abort_easyp2p(self, error_msg: str) -> None:
        """
        Abort the program in case of critical errors.

        Args:
            error_msg: Message to display to the user before aborting

        """
        self.progress_window.reject()
        QMessageBox.critical(
            self, "Kritischer Fehler", error_msg, QMessageBox.Close)
        sys.exit()
