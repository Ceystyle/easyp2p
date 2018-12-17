# -*- coding: utf-8 -*-

"""
Module implementing MainWindow, the main window of easyP2P
"""
import calendar
from datetime import date
import os
import p2p_parser
import p2p_results
import p2p_webdriver as wd
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QLineEdit, QCheckBox

from .Ui_main_window import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    This class defines the main window of easyP2P
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        Keyword Args:
        parent (QWidget): reference to the parent widget
        """
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.platforms =set([])
        self.start_month = date.today().month - 1
        self.comboBox_start_month.setCurrentIndex(self.comboBox_start_month.findText(wd.nbr_to_short_month(str(self.start_month))))
        self.start_year = date.today().year
        self.comboBox_start_year.setCurrentIndex(self.comboBox_start_year.findText(str(self.start_year)))
        self.end_month = date.today().month - 1
        self.comboBox_end_month.setCurrentIndex(self.comboBox_end_month.findText(wd.nbr_to_short_month(str(self.end_month))))
        self.end_year = date.today().year
        self.comboBox_end_year.setCurrentIndex(self.comboBox_end_year.findText(str(self.end_year)))
        self.set_start_date()
        self.set_end_date()
        self.output_file = os.getcwd() + '/P2P_Ergebnisse_{0}-{1}.xlsx'.format(self.start_date.strftime('%d.%m.%Y'), self.end_date.strftime('%d.%m.%Y'))
        self.on_lineEdit_output_file_textChanged(self.output_file)

    def set_start_date(self):
        self.start_date = date(self.start_year, self.start_month, 1)

    def set_end_date(self):
        self.end_date = date(self.end_year, self.end_month, calendar.monthrange(self.end_year, self.end_month)[1])
    
    @pyqtSlot(bool)
    def on_checkBox_Dofinance_toggled(self, checked):
        """
        Add/remove Dofinance to list of platforms for which account statements should be generated

        Args:        
            checked (bool): if True add Dofinance, if False remove Dofinance
        """
        if checked:
            self.platforms.add('Dofinance')
        else:
            self.platforms.remove('Dofinance')
    
    @pyqtSlot(bool)
    def on_checkBox_grupeer_toggled(self, checked):
        """
        Add/remove Grupeer to list of platforms for which account statements should be generated

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
        Add/remove Dofinance to list of platforms for which account statements should be generated

        Args:        
            checked (bool): if True add Dofinance, if False remove Dofinance
        """
        if checked:
            self.platforms.add('DoFinance')
        else:
            self.platforms.remove('DoFinance')
    
    @pyqtSlot(bool)
    def on_checkBox_Robocash_toggled(self, checked):
        """
        Add/remove Robocash to list of platforms for which account statements should be generated

        Args:        
            checked (bool): if True add Robocash, if False remove Robocash
        """
        if checked:
            self.platforms.add('Robocash')
        else:
            self.platforms.remove('Robocash')
    
    @pyqtSlot(bool)
    def on_checkBox_peerberry_toggled(self, checked):
        """
        Add/remove Peerberry to list of platforms for which account statements should be generated

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
        Add/remove Mintos to list of platforms for which account statements should be generated

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
        Add/remove Robocash to list of platforms for which account statements should be generated

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
        Add/remove Estateguru to list of platforms for which account statements should be generated

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
        Add/remove Swaper to list of platforms for which account statements should be generated

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
        Add/remove Twino to list of platforms for which account statements should be generated

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
        Update start date if the user changes start month in the combo box

        Args:        
            p0 (str): short month name chosen by the user in the combo box
        """
        self.start_month = int(wd.short_month_to_nbr(p0))
        self.set_start_date()
    
    @pyqtSlot(str)
    def on_comboBox_start_year_activated(self, p0):
        """
        Update start date if the user changes start year in the combo box

        Args:        
            p0 (str): year chosen by the user in the combo box
        """
        self.start_year = int(p0)
        self.set_start_date()
    
    @pyqtSlot(str)
    def on_comboBox_end_month_activated(self, p0):
        """
        Update end date if the user changes end month in the combo box

        Args:        
            p0 (str): short month name chosen by the user in the combo box
        """
        self.end_month = int(wd.short_month_to_nbr(p0))
        self.set_end_date()
    
    @pyqtSlot(str)
    def on_comboBox_end_year_activated(self, p0):
        """
        Update end date if the user changes end year in the combo box

        Args:        
            p0 (str): year chosen by the user in the combo box
        """
        self.end_year = int(p0)
        self.set_end_date()
    
    @pyqtSlot()
    def on_pushButton_start_clicked(self):
        """
        Start evaluation for the chosen P2P platforms and the given date range. Show the results for all P2P platforms for which account
        statement generation was successful.
        """
        #Check that start date is before end date
        if self.start_date > self.end_date:
            print('Startdatum liegt nach Enddatum!')
            return

        # Check if download directory exists, if not create it
        dl_location = './p2p_downloads'
        if not os.path.isdir(dl_location):
            os.makedirs(dl_location)

        list_of_dfs = []

        for platform in self.platforms:
            try:
                func = getattr(wd, 'open_selenium_'+platform.lower())
            except AttributeError:
                print('Die Funktion zum Öffnen von {0} konnte nicht gefunden werden. Ist p2p_webdriver.py vorhanden?'\
                    .format(platform))
            else:
                if func(self.start_date,  self.end_date) < 0:
                    print('{0} wird nicht im Ergebnis berücksichtigt'.format(platform))
                else:
                    try:
                        parser = getattr(p2p_parser, platform.lower())
                    except AttributeError:
                        print('Der Parser für {0} konnte nicht gefunden werden. Ist p2p_parser.py vorhanden?'.format(platform))
                    else:
                        df = parser()
                        list_of_dfs.append(df)

        df_result = p2p_results.combine_dfs(list_of_dfs)
        p2p_results.show_results(df_result,  self.start_date,  self.end_date, self.output_file)
    
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
        Open dialog window for changing the save location of the results file
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.output_file, _ = QFileDialog.getSaveFileName(self, "Ausgabedatei wählen", self.output_file, "MS Excel Dateien (*.xlsx)", options=options)
        if self.output_file:
            self.on_lineEdit_output_file_textChanged(self.output_file)
    
    @pyqtSlot(bool)
    def on_checkBox_select_all_toggled(self, checked):
        """
        Toggle/untoggle all P2P platforms

        Args:        
            checked (bool): if True toggle all check boxes, if False untoggle all check boxes
        """
        for check_box in self.groupBox_platforms.findChildren(QCheckBox):
            check_box.setChecked(checked)
