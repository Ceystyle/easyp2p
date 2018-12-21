# -*- coding: utf-8 -*-

"""Module implementing MainWindow, the main window of easyP2P."""

import calendar
from datetime import date
import os
import p2p_parser
import p2p_results
import p2p_webdriver as wd
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QLineEdit, QCheckBox
from PyQt5.QtWidgets import QMessageBox
from xlrd.biffh import XLRDError

from .Ui_main_window import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    """This class defines the main window of easyP2P."""

    def __init__(self, parent=None):
        """
        Constructor.

        Keyword Args:
        parent (QWidget): reference to the parent widget

        """
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.progressWindow = None
        self.worker = None
        self.platforms = set([])
        self.start_month = date.today().month - 1
        self.comboBox_start_month.setCurrentIndex(
            self.comboBox_start_month.findText(
                wd.nbr_to_short_month(str(self.start_month))))
        self.start_year = date.today().year
        self.comboBox_start_year.setCurrentIndex(
            self.comboBox_start_year.findText(str(self.start_year)))
        self.end_month = date.today().month - 1
        self.comboBox_end_month.setCurrentIndex(
            self.comboBox_end_month.findText(
                wd.nbr_to_short_month(str(self.end_month))))
        self.end_year = date.today().year
        self.comboBox_end_year.setCurrentIndex(
            self.comboBox_end_year.findText(str(self.end_year)))
        self.set_start_date()
        self.set_end_date()
        self.output_file = os.getcwd() + '/P2P_Ergebnisse_{0}-{1}.xlsx'.format(
            self.start_date.strftime('%d.%m.%Y'),
            self.end_date.strftime('%d.%m.%Y'))
        self.on_lineEdit_output_file_textChanged(self.output_file)

    def set_start_date(self):
        """Helper method to set start date to first day of selected month."""
        self.start_date = date(self.start_year, self.start_month, 1)

    def set_end_date(self):
        """Helper method to set end date to last day of selected month."""
        end_of_month = calendar.monthrange(self.end_year, self.end_month)[1]
        self.end_date = date(self.end_year, self.end_month, end_of_month)

    @pyqtSlot(bool)
    def on_checkBox_bondora_toggled(self, checked):
        """
        Add/remove Bondora to list of platforms.

        Args:
            checked (bool): if True add Bondora, if False remove Bondora

        """
        if checked:
            self.platforms.add('Bondora')
        else:
            self.platforms.remove('Bondora')

    @pyqtSlot(bool)
    def on_checkBox_grupeer_toggled(self, checked):
        """
        Add/remove Grupeer to list of platforms.

        Args:
            checked (bool): if True add Grupeer, if False remove Grupeer

        """
        if checked:
            self.platforms.add('Grupeer')
        else:
            self.platforms.remove('Grupeer')

    @pyqtSlot(bool)
    def on_checkBox_dofinance_toggled(self, checked):
        """
        Add/remove Dofinance to list of platforms.

        Args:
            checked (bool): if True add Dofinance, if False remove Dofinance

        """
        if checked:
            self.platforms.add('DoFinance')
        else:
            self.platforms.remove('DoFinance')

    @pyqtSlot(bool)
    def on_checkBox_iuvo_toggled(self, checked):
        """
        Add/remove Iuvo to list of platforms.

        Args:
            checked (bool): if True add Iuvo, if False remove Iuvo

        """
        if checked:
            self.platforms.add('Iuvo')
        else:
            self.platforms.remove('Iuvo')

    @pyqtSlot(bool)
    def on_checkBox_peerberry_toggled(self, checked):
        """
        Add/remove Peerberry to list of platforms.

        Args:
            checked (bool): if True add Peerberry, if False remove Peerberry

        """
        if checked:
            self.platforms.add('PeerBerry')
        else:
            self.platforms.remove('PeerBerry')

    @pyqtSlot(bool)
    def on_checkBox_mintos_toggled(self, checked):
        """
        Add/remove Mintos to list of platforms.

        Args:
            checked (bool): if True add Mintos, if False remove Mintos

        """
        if checked:
            self.platforms.add('Mintos')
        else:
            self.platforms.remove('Mintos')

    @pyqtSlot(bool)
    def on_checkBox_robocash_toggled(self, checked):
        """
        Add/remove Robocash to list of platforms.

        Args:
            checked (bool): if True add Robocash, if False remove Robocash

        """
        if checked:
            self.platforms.add('Robocash')
        else:
            self.platforms.remove('Robocash')

    @pyqtSlot(bool)
    def on_checkBox_estateguru_toggled(self, checked):
        """
        Add/remove Estateguru to list of platforms.

        Args:
            checked (bool): if True add Estateguru, if False remove Estateguru

        """
        if checked:
            self.platforms.add('Estateguru')
        else:
            self.platforms.remove('Estateguru')

    @pyqtSlot(bool)
    def on_checkBox_swaper_toggled(self, checked):
        """
        Add/remove Swaper to list of platforms.

        Args:
            checked (bool): if True add Swaper, if False remove Swaper

        """
        if checked:
            self.platforms.add('Swaper')
        else:
            self.platforms.remove('Swaper')

    @pyqtSlot(bool)
    def on_checkBox_twino_toggled(self, checked):
        """
        Add/remove Twino to list of platforms.

        Args:
            checked (bool): if True add Twino, if False remove Twino

        """
        if checked:
            self.platforms.add('Twino')
        else:
            self.platforms.remove('Twino')

    @pyqtSlot(str)
    def on_comboBox_start_month_activated(self, p0):
        """
        Update start date if the user changed start month in the combo box.

        Args:
            p0 (str): short month name chosen by the user in the combo box

        """
        self.start_month = int(wd.short_month_to_nbr(p0))
        self.set_start_date()

    @pyqtSlot(str)
    def on_comboBox_start_year_activated(self, p0):
        """
        Update start date if the user changed start year in the combo box.

        Args:
            p0 (str): year chosen by the user in the combo box

        """
        self.start_year = int(p0)
        self.set_start_date()

    @pyqtSlot(str)
    def on_comboBox_end_month_activated(self, p0):
        """
        Update end date if the user changed end month in the combo box.

        Args:
            p0 (str): short month name chosen by the user in the combo box

        """
        self.end_month = int(wd.short_month_to_nbr(p0))
        self.set_end_date()

    @pyqtSlot(str)
    def on_comboBox_end_year_activated(self, p0):
        """
        Update end date if the user changed end year in the combo box.

        Args:
            p0 (str): year chosen by the user in the combo box

        """
        self.end_year = int(p0)
        self.set_end_date()

    @pyqtSlot()
    def on_pushButton_start_clicked(self):
        """
        Start evaluation for selected P2P platforms and the given date range.

        The evaluation will be done by a worker thread in class WorkerThread.
        Progress is tracked in ProgressWindow.

        """
        # Check that start date is before end date
        if self.start_date > self.end_date:
            QMessageBox.warning(
                self, 'Startdatum liegt nach Enddatum!',
                'Das Startdatum darf nicht nach dem Enddatum liegen!')
            return

        # Check that at least one platform is selected
        if len(self.platforms) == 0:
            QMessageBox.warning(
                self, 'Keine P2P Plattform ausgewählt!',
                'Bitte wähle mindestens eine P2P Plattform aus')
            return

        # Check if download directory exists, if not create it
        dl_location = './p2p_downloads'
        if not os.path.isdir(dl_location):
            os.makedirs(dl_location)

        self.worker = WorkerThread()
        self.worker.platforms = self.platforms
        self.worker.start_date = self.start_date
        self.worker.end_date = self.end_date
        self.worker.output_file = self.output_file
        self.abort = False
        self.worker.updateProgressBar.connect(self.updateProgressBar)
        self.worker.updateProgressText.connect(self.updateProgressText)
        self.worker.start()

        # Open progress window
        from ui.progress_window import ProgressWindow
        self.progressWindow = ProgressWindow()
        self.progressWindow.exec_()

        if self.progressWindow.result() == 0:
            self.worker.abort = True

    def updateProgressBar(self, value):
        """
        Updates the progress bar in ProgressWindow to new value.

        Args:
            value (float): value of the progress bar, between 0 and 100

        """
        if not (value >= 0 and value <= 100):
            error_message = ('Fortschrittsindikator beträgt: {0}. Er muss '
                             'zwischen 0 und 100 liegen!'.format(value))
            QMessageBox.warning(
                self, 'Fehler!', error_message)
            return

        self.progressWindow.progressBar.setValue(value)

    def updateProgressText(self, txt):
        """
        Appends a new line to the progress text in ProgressWindow.

        Args:
            txt (str): string to add to progress text

        """
        self.progressWindow.progressText.append(txt)

    @pyqtSlot(str)
    def on_lineEdit_output_file_textChanged(self, p0):
        """
        Update location where the results file should be saved.

        Args:
            p0 (str): file name entered by the user

        """
        QLineEdit.setText(self.lineEdit_output_file, p0)

    @pyqtSlot()
    def on_pushButton_file_chooser_clicked(self):
        """
        Open dialog window for changing the save location of the results file.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.output_file, _ = QFileDialog.getSaveFileName(
            self, "Ausgabedatei wählen", self.output_file,
            "MS Excel Dateien (*.xlsx)", options=options)
        if self.output_file:
            self.on_lineEdit_output_file_textChanged(self.output_file)

    @pyqtSlot(bool)
    def on_checkBox_select_all_toggled(self, checked):
        """
        Toggle/untoggle all P2P platforms.

        Args:
            checked (bool): if True toggle all check boxes, if False untoggle
                all check boxes

        """
        for check_box in self.groupBox_platforms.findChildren(QCheckBox):
            check_box.setChecked(checked)

class WorkerThread(QThread):

    """
    Worker thread to offload calls to p2p_webdriver, p2p_parser, p2p_results.

    This class is responsible for accessing the P2P platform methods in
    p2p_webdriver and to prepare the results. The main reason for separating
    the calls to p2p_webdriver, p2p_parser and p2p_results from the main thread
    is to keep the GUI responsive while the webdriver is working.

    """

    # Signals for communicating with the MainWindow
    updateProgressBar = pyqtSignal(float)
    updateProgressText = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        Constructor.

        Keyword Args:
            parent (QThread): reference to the parent thread

        """
        super(WorkerThread, self).__init__(parent)
        self.abort = False

    def get_p2p_function(self, platform):
        """
        Helper method to get the name of the appropriate webdriver function.

        Args:
            platform (str): name of the P2P platform

        Returns:
            function: p2p_webdriver.open_selenium_* function for handling this
            P2P platform or None if the function cannot be found

        """
        try:
            func = getattr(wd, 'open_selenium_'+platform.lower())
        except AttributeError:
            error_message = (
                'Funktion zum Öffnen von {0} konnte nicht gefunden werden. '
                'Ist p2p_webdriver.py vorhanden?'.format(platform))
            self.updateProgressText.emit(error_message)
            return None
        else:
            return func

    def get_p2p_parser(self, platform):
        """
        Helper method to get the name of the appropriate parser.

        Args:
            platform (str): name of the P2P platform

        Returns:
            function: p2p_parser.* function for parsing this P2P platform or
            None if the function cannot be found

        """
        try:
            parser = getattr(p2p_parser, platform.lower())
        except AttributeError:
            error_message = (
                'Parser für {0} konnte nicht gefunden werden. '
                'Ist p2p_parser.py vorhanden?'.format(platform))
            self.updateProgressText.emit(error_message)
            return None
        else:
            return parser

    def run(self):
        """
        Gets and outputs results from all selected P2P platforms.

        Iterates over all selected P2P platforms, gets the results from
        p2p_webdriver and outputs the results. After each platform the progress
        bar is increased.

        """
        list_of_dfs = []
        progress = 0
        # Distribute 95% evenly across all selected platforms
        # The last 5 percent are for preparing the results
        step = 95/len(self.platforms)

        for platform in self.platforms:
            if self.abort:
                return

            func = self.get_p2p_function(platform)
            if func is None:
                continue

            self.updateProgressText.emit(
                'Start der Auswertung von {0}...'.format(platform))
            if func(self.start_date,  self.end_date) < 0:
                error_message = ('Es ist ein Fehler aufgetreten! {0} wird '
                    'nicht im Ergebnis berücksichtigt'.format(platform))
                self.updateProgressText.emit(error_message)
            else:
                if self.abort:
                    return

                progress += step
                self.updateProgressBar.emit(progress)
                self.updateProgressText.emit(
                    '{0} erfolgreich ausgewertet!'.format(platform))

                parser = self.get_p2p_parser(platform)
                if parser is None:
                    continue

                try:
                    df = parser()[0]
                    list_of_dfs.append(df)
                except FileNotFoundError:
                    error_message = ('Der heruntergeladene {0}-Kontoauszug '
                        'konnte nicht gefunden werden!'.format(platform))
                    self.updateProgressText.emit(error_message)
                    warning_message = '{0} wird ignoriert!'.format(platform)
                    self.updateProgressText.emit(warning_message)
                    continue
                except XLRDError:
                    error_message = ('Der heruntergeladene {0}-Kontoauszug '
                        'ist beschädigt!'.format(platform))
                    self.updateProgressText.emit(error_message)
                    warning_message = '{0} wird ignoriert!'.format(platform)
                    self.updateProgressText.emit(warning_message)
                    continue
                else:
                    if len(parser()[1]) > 0:
                        warning_message = ('{0}: unbekannter Cashflow-Typ '
                            'wird im Ergebnis ignoriert: {1}'.format(
                                platform, parser()[1]))
                        self.updateProgressText.emit(warning_message)

        if self.abort:
            return

        df_result = p2p_results.combine_dfs(list_of_dfs)

        if p2p_results.show_results(
                df_result, self.start_date,
                self.end_date, self.output_file) < 0:
            error_message = ('Keine Ergebnisse vorhanden')
            self.updateProgressText.emit(error_message)

        self.updateProgressBar.emit(100)
