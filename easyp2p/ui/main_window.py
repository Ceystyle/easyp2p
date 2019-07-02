# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Application for downloading and presenting investment results for
several people-to-people (P2P) lending platforms.

"""

from datetime import date, timedelta
import gc
import os
from pathlib import Path
import sys
from typing import Set

from PyQt5.QtCore import (
    pyqtSlot, QCoreApplication, QLocale, QTranslator, QLibraryInfo)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QLineEdit, QCheckBox, QMessageBox)

import easyp2p
from easyp2p.p2p_settings import Settings
from easyp2p.p2p_signals import Signals
from easyp2p.ui.progress_window import ProgressWindow
from easyp2p.ui.settings_window import SettingsWindow
from easyp2p.ui.Ui_main_window import Ui_MainWindow

_translate = QCoreApplication.translate

name = 'easyp2p'  # pylint: disable=invalid-name


class MainWindow(QMainWindow, Ui_MainWindow):

    """This class defines the main window of easyp2p."""

    def __init__(self, app: QApplication) -> None:
        """Constructor of MainWindow."""
        super().__init__()
        self.setupUi(self)
        self._app = app
        self._translator = QTranslator()
        self._qttranslator = QTranslator()
        end_last_month = date.today().replace(day=1) - timedelta(days=1)
        self.date_range = (end_last_month.replace(day=1), end_last_month)
        self.set_language()
        self.output_file_changed = False
        self.set_output_file()
        self.settings = Settings(
            self.date_range, self.line_edit_output_file.text())

    def init_date_combo_boxes(self) -> None:
        """Set the items for all date combo boxes."""
        month_list = [
            QLocale(QLocale().name()).monthName(i, 1) for i in range(1, 13)]
        year_list = [str(year) for year in range(2010, date.today().year + 1)]
        for i, combo_box in zip(
                range(2),
                [self.combo_box_start_month, self.combo_box_end_month]):
            combo_box.clear()
            combo_box.addItems(month_list)
            combo_box.setCurrentIndex(self.date_range[i].month - 1)
        for i, combo_box in zip(
                range(2), [self.combo_box_start_year, self.combo_box_end_year]):
            combo_box.clear()
            combo_box.addItems(year_list)
            combo_box.setCurrentIndex(self.date_range[i].year - 2010)

    def set_language(self, locale: str = None) -> None:
        """
        Translate GUI into language of locale.

        Args:
            locale: Locale into which the GUI must be translated. If None the
                system locale will be used.

        """
        if not locale:
            locale = QLocale().name()
        QLocale.setDefault(QLocale(locale))
        if locale.startswith('de'):
            self.action_english.setChecked(False)
            self.action_german.setChecked(True)
        else:
            self.action_english.setChecked(True)
            self.action_german.setChecked(False)
        self._translator.load('easyp2p_' + locale, os.path.join(
            easyp2p.__path__[0], 'i18n', 'ts'))
        self._app.installTranslator(self._translator)
        self._qttranslator.load(
            'qtbase_' + locale, QLibraryInfo.location(
                QLibraryInfo.TranslationsPath))
        self._app.installTranslator(self._qttranslator)
        self.retranslateUi(self)
        self.init_date_combo_boxes()

    def set_date_range(self) -> None:
        """Set currently in combo boxes selected date range."""
        start_month = self.combo_box_start_month.currentText()
        start_year = self.combo_box_start_year.currentText()
        start_date = QLocale().toDate('1'+start_month+start_year, 'dMMMyyyy')
        end_month = self.combo_box_end_month.currentText()
        end_year = self.combo_box_end_year.currentText()
        end_date = QLocale().toDate('1'+end_month+end_year, 'dMMMyyyy')
        end_date.setDate(
            end_date.year(), end_date.month(), end_date.daysInMonth())
        self.date_range = (start_date.toPyDate(), end_date.toPyDate())
        self.set_output_file()

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
        if not self.output_file_changed:
            output_file = os.path.join(
                Path.home(),
                _translate('MainWindow', 'P2P_Results_{0}-{1}.xlsx').format(
                    self.date_range[0].strftime('%d%m%Y'),
                    self.date_range[1].strftime('%d%m%Y')))
            QLineEdit.setText(self.line_edit_output_file, output_file)

    @pyqtSlot(bool)
    def on_action_german_triggered(self):
        """Translate GUI to German."""
        self.set_language('de_de')

    @pyqtSlot(bool)
    def on_action_english_triggered(self):
        """Translate GUI to English."""
        self.set_language('en_US')

    @pyqtSlot(str)
    def on_combo_box_start_month_activated(self) -> None:
        """Update output file if user changed start month in the combo box."""
        self.set_date_range()

    @pyqtSlot(str)
    def on_combo_box_start_year_activated(self) -> None:
        """Update output file if user changed start year in the combo box."""
        self.set_date_range()

    @pyqtSlot(str)
    def on_combo_box_end_month_activated(self) -> None:
        """Update output file if user changed end month in the combo box."""
        self.set_date_range()

    @pyqtSlot(str)
    def on_combo_box_end_year_activated(self) -> None:
        """Update output file if user changed end year in the combo box."""
        self.set_date_range()

    @pyqtSlot()
    def on_push_button_file_chooser_clicked(self) -> None:
        """
        Open dialog window for changing the save location of the results file.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        output_file, _ = QFileDialog.getSaveFileName(
            self, _translate('MainWindow', 'Choose output file'),
            self.line_edit_output_file.text(),
            'MS Excel ' + _translate('MainWindow', 'files') + ' (*.xlsx)',
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
        # Make sure all abort flags are False in case the user aborted the
        # previous run
        for obj in gc.get_objects():
            if isinstance(obj, Signals):
                obj.abort = False
        platforms = self.get_platforms()

        # Check that start date is before end date
        if self.date_range[0] > self.date_range[1]:
            QMessageBox.warning(
                self,
                _translate('MainWindow', 'Start date is after end date!'),
                _translate(
                    'MainWindow',
                    'Start date must be before end date!'))
            return

        # Check that at least one platform is selected
        if not platforms:
            QMessageBox.warning(
                self, _translate(
                    'MainWindow', 'No P2P platform selected!'),
                _translate(
                   'MainWindow',
                   'Please choose at least one P2P platform!'))
            return

        self.settings.date_range = self.date_range
        self.settings.platforms = platforms
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


def main():
    """Open the main window of easyp2p."""
    app = QApplication(sys.argv)
    ui = MainWindow(app)  # pylint: disable=invalid-name
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
