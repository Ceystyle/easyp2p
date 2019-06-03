# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing MainWindow, the main window of easyp2p."""

import calendar
from datetime import date
import os
from pathlib import Path
from typing import Set, Tuple

from PyQt5.QtCore import pyqtSlot, QCoreApplication
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QLineEdit, QCheckBox, QMessageBox)

import easyp2p.p2p_helper as p2p_helper
from easyp2p.p2p_settings import Settings
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.settings_window import SettingsWindow
from easyp2p.ui.Ui_main_window import Ui_MainWindow

translate = QCoreApplication.translate


class MainWindow(QMainWindow, Ui_MainWindow):

    """This class defines the main window of easyp2p."""

    def __init__(self) -> None:
        """Constructor of MainWindow."""
        super().__init__()
        self.setupUi(self)
        # Initialize date combo boxes with previous month
        if date.today().month > 1:
            start_month = p2p_helper.nbr_to_short_month(
                str(date.today().month - 1))
            start_year = str(date.today().year)
        else:
            start_month = translate('MainWindow', 'Dec')
            start_year = str(date.today().year - 1)
        self.init_combo_boxes()
        self.set_date_range(start_month, start_year, start_month, start_year)
        self.output_file_changed = False
        self.set_output_file()
        self.settings = Settings(
            self.get_date_range(), self.line_edit_output_file.text())

    def init_combo_boxes(self):
        """Set the items for all date combo boxes."""
        month_list = [
            translate('MainWindow', 'Jan'),
            translate('MainWindow', 'Feb'),
            translate('MainWindow', 'Mar'),
            translate('MainWindow', 'Apr'),
            translate('MainWindow', 'May'),
            translate('MainWindow', 'Jun'),
            translate('MainWindow', 'Jul'),
            translate('MainWindow', 'Aug'),
            translate('MainWindow', 'Sep'),
            translate('MainWindow', 'Oct'),
            translate('MainWindow', 'Nov'),
            translate('MainWindow', 'Dec')]
        year_list = [str(year) for year in range(2010, date.today().year + 1)]
        self.combo_box_start_month.addItems(month_list)
        self.combo_box_end_month.addItems(month_list)
        self.combo_box_start_year.addItems(year_list)
        self.combo_box_end_year.addItems(year_list)

    def set_date_range(
            self, start_month: str, start_year: str,
            end_month: str, end_year: str) -> None:
        """
        Set start and end dates in the combo boxes.

        Args:
            start_month: Start month
            start_year: Start year
            end_month: End month
            end_year: End year

        """
        self.combo_box_start_month.setCurrentIndex(
            self.combo_box_start_month.findText(start_month))
        self.combo_box_start_year.setCurrentIndex(
            self.combo_box_start_year.findText(start_year))
        self.combo_box_end_month.setCurrentIndex(
            self.combo_box_end_month.findText(end_month))
        self.combo_box_end_year.setCurrentIndex(
            self.combo_box_end_year.findText(end_year))

    def get_date_range(self) -> Tuple[date, date]:
        """
        Get currently selected date range from combo boxes.

        Returns:
            Date range (start_date, end_date)

        """
        start_month = int(p2p_helper.short_month_to_nbr(
            str(self.combo_box_start_month.currentText())))
        start_year = int(self.combo_box_start_year.currentText())
        end_month = int(p2p_helper.short_month_to_nbr(
            str(self.combo_box_end_month.currentText())))
        end_year = int(self.combo_box_end_year.currentText())
        last_day_of_month = calendar.monthrange(end_year, end_month)[1]
        return (date(start_year, start_month, 1),
                date(end_year, end_month, last_day_of_month))

    def get_platforms(self, checked: bool = True) -> Set[str]:
        """
        Get list of all platforms selected by the user.

        Keyword Args:
            checked: If True only the platforms selected by the user will
                be returned, if False all platforms will be returned

        Returns:
            Set of P2P platform names

        """
        platforms = set()
        for check_box in self.group_box_platforms.findChildren(QCheckBox):
            if not checked:
                platforms.add(check_box.text().replace('&', ''))
            elif check_box.isChecked():
                platforms.add(check_box.text().replace('&', ''))
        return platforms

    def set_output_file(self) -> None:
        """Helper method to set the name of the output file."""
        date_range = self.get_date_range()
        if not self.output_file_changed:
            output_file = os.path.join(
                 Path.home(), translate('MainWindow', 'P2P_Results') \
                    + '_{0}-{1}.xlsx'.format(
                    date_range[0].strftime('%d%m%Y'),
                    date_range[1].strftime('%d%m%Y')))
            QLineEdit.setText(self.line_edit_output_file, output_file)

    @pyqtSlot(str)
    def on_combo_box_start_month_activated(self) -> None:
        """Update output file if user changed start month in the combo box."""
        self.set_output_file()

    @pyqtSlot(str)
    def on_combo_box_start_year_activated(self) -> None:
        """Update output file if user changed start year in the combo box."""
        self.set_output_file()

    @pyqtSlot(str)
    def on_combo_box_end_month_activated(self) -> None:
        """Update output file if user changed end month in the combo box."""
        self.set_output_file()

    @pyqtSlot(str)
    def on_combo_box_end_year_activated(self) -> None:
        """Update output file if user changed end year in the combo box."""
        self.set_output_file()

    @pyqtSlot()
    def on_push_button_file_chooser_clicked(self) -> None:
        """
        Open dialog window for changing the save location of the results file.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        output_file, _ = QFileDialog.getSaveFileName(
            self, translate('MainWindow', 'Choose output file'),
            self.line_edit_output_file.text(),
            'MS Excel ' + translate('MainWindow', 'files') + ' (*.xlsx)',
            options=options)
        if output_file:
            # The file name must include xlsx file format. Otherwise the Excel
            # writer will crash later.
            if not output_file.endswith('.xlsx'):
                output_file += '.xlsx'
            QLineEdit.setText(self.line_edit_output_file, output_file)
            self.output_file_changed = True

    @pyqtSlot(bool)
    def on_check_box_select_all_toggled(self, checked: bool) -> None:
        """
        Toggle/untoggle all P2P platforms.

        Args:
            checked: if True toggle all check boxes, if False untoggle
                all check boxes

        """
        for check_box in self.group_box_platforms.findChildren(QCheckBox):
            check_box.setChecked(checked)

    @pyqtSlot()
    def on_push_button_start_clicked(self) -> None:
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
                self,
                translate('MainWindow', 'Start date is after end date!'),
                translate(
                    'MainWindow',
                    'Start date must be before end date!'))
            return

        # Check that at least one platform is selected
        if not platforms:
            QMessageBox.warning(
                self, translate(
                    'MainWindow', 'No P2P platform selected!'),
               translate(
                   'MainWindow',
                   'Please choose at least one P2P platform!'))
            return

        self.settings.date_range = self.get_date_range()
        self.settings.platforms = self.get_platforms()
        self.settings.output_file = self.line_edit_output_file.text()

        # Open progress window
        progress_window = ProgressWindow(self.settings)
        progress_window.exec_()

    @pyqtSlot()
    def on_tool_button_settings_clicked(self) -> None:
        """Open the settings window."""
        settings_window = SettingsWindow(
            self.get_platforms(False), self.settings)
        settings_window.exec_()
