# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
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
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
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

    def set_start_date(self):
        self.start_date = date(self.start_year, self.start_month, 1)

    def set_end_date(self):
        self.end_date = date(self.end_year, self.end_month, calendar.monthrange(self.end_year, self.end_month)[1])
    
    @pyqtSlot(bool)
    def on_checkBox_bondora_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Bondora')
        else:
            self.platforms.remove('Bondora')
    
    @pyqtSlot(bool)
    def on_checkBox_grupeer_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Grupeer')
        else:
            self.platforms.remove('Grupeer')
    
    @pyqtSlot(bool)
    def on_checkBox_dofinance_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('DoFinance')
        else:
            self.platforms.remove('DoFinance')
    
    @pyqtSlot(bool)
    def on_checkBox_iuvo_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Iuvo')
        else:
            self.platforms.remove('Iuvo')
    
    @pyqtSlot(bool)
    def on_checkBox_peerberry_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('PeerBerry')
        else:
            self.platforms.remove('PeerBerry')
    
    @pyqtSlot(bool)
    def on_checkBox_mintos_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Mintos')
        else:
            self.platforms.remove('Mintos')
    
    @pyqtSlot(bool)
    def on_checkBox_robocash_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Robocash')
        else:
            self.platforms.remove('Robocash')
    
    @pyqtSlot(bool)
    def on_checkBox_estateguru_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Estateguru')
        else:
            self.platforms.remove('Estateguru')
    
    @pyqtSlot(bool)
    def on_checkBox_swaper_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Swaper')
        else:
            self.platforms.remove('Swaper')
    
    @pyqtSlot(bool)
    def on_checkBox_twino_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.platforms.add('Twino')
        else:
            self.platforms.remove('Twino')

    @pyqtSlot(str)
    def on_comboBox_start_month_activated(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        self.start_month = int(wd.short_month_to_nbr(p0))
        self.set_start_date()
    
    @pyqtSlot(str)
    def on_comboBox_start_year_activated(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        self.start_year = int(p0)
        self.set_start_date()
    
    @pyqtSlot(str)
    def on_comboBox_end_month_activated(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        self.end_month = int(wd.short_month_to_nbr(p0))
        self.set_end_date()
    
    @pyqtSlot(str)
    def on_comboBox_end_year_activated(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        self.end_year = int(p0)
        self.set_end_date()
    
    @pyqtSlot()
    def on_pushButton_start_clicked(self):
        """
        Slot documentation goes here.
        """
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
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        QLineEdit.setText(self.lineEdit_output_file, p0)
    
    @pyqtSlot()
    def on_pushButton_file_chooser_clicked(self):
        """
        Slot documentation goes here.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        default_name = 'P2P_Ergebnisse_{0}-{1}.xlsx'.format(self.start_date.strftime('%d.%m.%Y'), self.end_date.strftime('%d.%m.%Y'))
        self.output_file, _ = QFileDialog.getSaveFileName(self, "Ausgabedatei wählen", default_name, "MS Excel Dateien (*.xlsx)", options=options)
        if self.output_file:
            self.on_lineEdit_output_file_textChanged(self.output_file)
    
    @pyqtSlot(bool)
    def on_checkBox_select_all_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        for check_box in self.groupBox_platforms.findChildren(QCheckBox):
            check_box.setChecked(checked)
