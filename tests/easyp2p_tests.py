# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all tests for easyP2P"""

from datetime import date
import sys
from typing import Tuple
import unittest

import keyring
import pandas as pd
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest

from context import *

PLATFORMS = {
    'Bondora': 'csv',
    'DoFinance': 'xlsx',
    'Estateguru': 'csv',
    'Grupeer': 'xlsx',
    'Iuvo': 'xlsx',
    'Mintos': 'xlsx',
    'PeerBerry': 'csv',
    'Robocash': 'xls',
    'Swaper': 'xlsx',
    'Twino': 'xlsx'}
INPUT_PREFIX = 'input/input_test_'
RESULT_PREFIX = 'results/result_test_'

app = QApplication(sys.argv)

class MainWindowTests(unittest.TestCase):
    """Test the main window of easyP2P"""
    def setUp(self) -> None:
        """Create the GUI"""
        self.form = MainWindow()
        self.message_box_open = False
        self.progress_window_open = False

    def set_test_dates(self) -> None:
        """Sets start and end dates in the GUI."""
        self.form.comboBox_start_month.setCurrentIndex(
            self.form.comboBox_start_month.findText('Sep'))
        self.form.comboBox_start_year.setCurrentIndex(
            self.form.comboBox_start_month.findText('2018'))
        self.form.comboBox_end_month.setCurrentIndex(
            self.form.comboBox_start_month.findText('Dez'))
        self.form.comboBox_end_year.setCurrentIndex(
            self.form.comboBox_start_month.findText('2018'))

    def test_defaults(self) -> None:
        """Test GUI in default state"""

        # All checkboxes are unchecked in default state
        self.assertFalse(self.form.checkBox_bondora.isChecked())
        self.assertFalse(self.form.checkBox_dofinance.isChecked())
        self.assertFalse(self.form.checkBox_estateguru.isChecked())
        self.assertFalse(self.form.checkBox_grupeer.isChecked())
        self.assertFalse(self.form.checkBox_iuvo.isChecked())
        self.assertFalse(self.form.checkBox_mintos.isChecked())
        self.assertFalse(self.form.checkBox_peerberry.isChecked())
        self.assertFalse(self.form.checkBox_robocash.isChecked())
        self.assertFalse(self.form.checkBox_select_all.isChecked())
        self.assertFalse(self.form.checkBox_swaper.isChecked())
        self.assertFalse(self.form.checkBox_twino.isChecked())
        #TODO: add tests for comboBoxes and output file name

    def test_select_all_platforms(self) -> None:
        """Test the Select All Platforms checkbox"""
        # Toggle the 'Select all platforms' checkbox
        self.form.checkBox_select_all.setChecked(True)

        # Test that all platform check boxes are checked
        self.assertTrue(self.form.checkBox_bondora.isChecked())
        self.assertTrue(self.form.checkBox_dofinance.isChecked())
        self.assertTrue(self.form.checkBox_estateguru.isChecked())
        self.assertTrue(self.form.checkBox_grupeer.isChecked())
        self.assertTrue(self.form.checkBox_iuvo.isChecked())
        self.assertTrue(self.form.checkBox_mintos.isChecked())
        self.assertTrue(self.form.checkBox_peerberry.isChecked())
        self.assertTrue(self.form.checkBox_robocash.isChecked())
        self.assertTrue(self.form.checkBox_select_all.isChecked())
        self.assertTrue(self.form.checkBox_swaper.isChecked())
        self.assertTrue(self.form.checkBox_twino.isChecked())

        # Test if the platform list is correct
        self.assertEqual(self.form.platforms, PLATFORMS.keys())

    def test_no_platform_selected(self) -> None:
        """Test clicking start without any selected platform"""
        # Push the start button without selecting any platform first
        QTimer.singleShot(500, self.is_message_box_open)
        self.form.pushButton_start.click()

        # Check that a warning message pops up
        self.assertTrue(self.message_box_open)

        # Check that the progress window did not open
        self.assertFalse(self.progress_window_open)

    def is_message_box_open(self) -> bool:
        """Helper method to determine if a QMessageBox is open."""
        allToplevelWidgets = QApplication.topLevelWidgets()
        for widget in allToplevelWidgets:
            if isinstance(widget, QMessageBox):
                self.message_box_open = True
                QTest.keyClick(widget, Qt.Key_Enter)

    def is_progress_window_open(self):
        """Helper method to determine if a ProgressWindow is open."""
        allToplevelWidgets = QApplication.topLevelWidgets()
        for widget in allToplevelWidgets:
            if isinstance(widget, ProgressWindow):
                self.progress_window_open = True


class ProgressWindowTests(unittest.TestCase):
    """Test the progress window of easyP2P"""
    def setup_gui(self):
        """Initialize ProgressWindow"""
        self.form = ProgressWindow()

    def test_defaults(self):
        """Test default behaviour of ProgressWindow"""
        self.setup_gui()
        self.assertEqual(self.form.progressBar.value(), 0)
        self.assertEqual(self.form.progressText.isReadOnly(), True)
        self.assertEqual(self.form.progressText.toPlainText(), '')
        self.assertEqual(self.form.pushButton_ok.isEnabled(), False)
        self.assertEqual(self.form.pushButton_abort.isEnabled(), True)


class PlatformTests(unittest.TestCase):
    """Test p2p_platforms"""
    def setUp(self):
        """Initializes the default date ranges for the tests."""
        self.date_range = (date(2018, 9, 1), date(2018, 12, 31))
        self.date_range_no_cfs = (date(2016, 9, 1), date(2016, 12, 31))

    def get_credentials_from_keyring(self, platform: str) -> Tuple[str, str]:
        """
        Helper method to get credentials from the keyring.

        Args:
            platform (str): Name of the P2P platform

        Returns:
            Tuple[str, str]: (username, password) for the P2P platform

        """
        if keyring.get_keyring():
            try:
                username = keyring.get_password(platform, 'username')
                password = keyring.get_password(platform, username)
            except TypeError:
                self.skipTest(
                    'No credentials for {0} in the keyring.'.format(platform))

        return (username, password)

    def test_download_bondora_statement(self) -> None:
        """Test download_bondora_statement"""
        credentials = self.get_credentials_from_keyring('Bondora')
        bondora.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            RESULT_PREFIX + 'download_bondora_statement.csv'))

    def test_download_bondora_statement_no_cfs(self) -> None:
        """
        Test download_bondora_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('Bondora')
        bondora.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            RESULT_PREFIX + 'download_bondora_statement_no_cfs.csv'))

    def test_download_dofinance_statement(self):
        """Test download_dofinance_statement function"""
        credentials = self.get_credentials_from_keyring('DoFinance')
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        dofinance.download_statement(
            dofinance_date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/dofinance_statement.xlsx',
            RESULT_PREFIX + 'download_dofinance_statement.xlsx'))

    def test_download_dofinance_statement_no_cfs(self):
        """
        Test download_dofinance_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('DoFinance')
        dofinance.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/dofinance_statement.xlsx',
            RESULT_PREFIX +'download_dofinance_statement_no_cfs.xlsx'))

    def test_download_estateguru_statement(self):
        """Test download_estateguru_statement"""
        credentials = self.get_credentials_from_keyring('Estateguru')
        estateguru.download_statement(
            self.date_range, credentials)
        # The Estateguru statement contains all cashflows ever generated for
        # this account. Therefore it changes regularly and we cannot compare
        # it to a fixed reference file. This test just makes sure that the
        # statement was downloaded.
        # TODO: check for content errors
        self.assertTrue(os.path.isfile(
            'p2p_downloads/estateguru_statement.csv'))

    def test_download_grupeer_statement(self):
        """Test download_grupeer_statement"""
        credentials = self.get_credentials_from_keyring('Grupeer')
        grupeer.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/grupeer_statement.xlsx',
            RESULT_PREFIX + 'download_grupeer_statement.xlsx'))

    def test_download_grupeer_statement_no_cfs(self):
        """
        Test download_grupeer_statement if there are no cashflows in date_range
        """
        credentials = self.get_credentials_from_keyring('Grupeer')
        grupeer.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/grupeer_statement.xlsx',
            RESULT_PREFIX + 'download_grupeer_statement_no_cfs.xlsx'))

    def test_download_iuvo_statement(self):
        """Test download_iuvo_statement"""
        credentials = self.get_credentials_from_keyring('Iuvo')
        iuvo.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/iuvo_statement.csv',
            RESULT_PREFIX + 'download_iuvo_statement.csv'))

    def test_download_iuvo_statement_no_cfs(self):
        """
        Test download_iuvo_statement when there are no cashflows in
        date_range
        """
        credentials = self.get_credentials_from_keyring('Iuvo')
        iuvo.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/iuvo_statement.csv',
            RESULT_PREFIX + 'download_iuvo_statement_no_cfs.csv'))

    def test_download_mintos_statement(self):
        """Test download_mintos_statement"""
        credentials = self.get_credentials_from_keyring('Mintos')
        mintos.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/mintos_statement.xlsx',
            RESULT_PREFIX + 'download_mintos_statement.xlsx'))

    def test_download_mintos_statement_no_cfs(self):
        """
        Test download_mintos_statement when there is no cashflow in date_range
        """
        credentials = self.get_credentials_from_keyring('Mintos')
        mintos.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/mintos_statement.xlsx',
            RESULT_PREFIX + 'download_mintos_statement_no_cfs.xlsx'))

    def test_download_peerberry_statement(self):
        """Test download_peerberry_statement"""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        peerberry.download_statement(
            self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/peerberry_statement.csv',
            RESULT_PREFIX + 'download_peerberry_statement.csv'))

    def test_download_peerberry_statement_no_cfs(self):
        """
        Test download_peerberry_statement when there is no cashflow in
        date_range
        """
        credentials = self.get_credentials_from_keyring('PeerBerry')
        peerberry.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/peerberry_statement.csv',
            RESULT_PREFIX + 'download_peerberry_statement_no_cfs.csv'))

    def test_download_robocash_statement(self):
        """Test download_robocash_statement function"""
        credentials = self.get_credentials_from_keyring('Robocash')
        robocash.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/robocash_statement.xls',
            RESULT_PREFIX + 'download_robocash_statement.xls'))

    def test_download_robocash_statement_no_cfs(self):
        """
        Test download_robocash_statement function when there is no cashflow in
        date_range
        """
        credentials = self.get_credentials_from_keyring('Robocash')
        robocash.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/robocash_statement.xls',
            RESULT_PREFIX + 'download_robocash_statement_no_cfs.xls'))

    def test_download_swaper_statement(self):
        """Test download_swaper_statement function"""
        credentials = self.get_credentials_from_keyring('Swaper')
        swaper.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/swaper_statement.xlsx',
            RESULT_PREFIX + 'download_swaper_statement.xlsx'))

    def test_download_swaper_statement_no_cfs(self) -> None:
        """
        Test download_swaper_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('Swaper')
        swaper.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/swaper_statement.xlsx',
            RESULT_PREFIX + 'download_swaper_statement_no_cfs.xlsx'))

    def test_download_twino_statement(self):
        """Test download_twino_statement"""
        credentials = self.get_credentials_from_keyring('Twino')
        twino.download_statement(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/twino_statement.xlsx',
            RESULT_PREFIX + 'download_twino_statement.xlsx',
            drop_header=True))

    def test_download_twino_statement_no_cfs(self):
        """
        Test download_twino_statement when no cashflows exist in date range
        """
        credentials = self.get_credentials_from_keyring('Twino')
        twino.download_statement(
            self.date_range_no_cfs, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/twino_statement.xlsx',
            RESULT_PREFIX + 'download_twino_statement_no_cfs.xlsx',
            drop_header=True))


class P2PParserTests(unittest.TestCase):
    """Test p2p_parser"""
    def setUp(self):
        """Initializes the default arguments for p2p_parser."""
        self.date_range = (date(2018, 9, 1), date(2018, 12, 31))
        self.date_range_missing_month = (date(2018, 8, 1), date(2018, 12, 31))
        self.date_range_no_cfs = (date(2016, 9, 1), date(2016, 12, 31))

    def run_parser_test(
            self, platform: str, input_file: str,
            exp_result_file: str,
            date_range: Tuple[date, date] = \
                (date(2018, 9, 1), date(2018, 12, 31)),
            unknown_cf_types_exp: str = '') -> None:
        """
        Test the parser of the given platform.

        In order to run these tests the known correct results need to be saved
        in exp_result_file first.

        Args:
            platform (str): Name of the P2P platform
            input_file (str): input file for the parser
            exp_result_file (str): file with expected results

        Keyword Args:
            unknown_cf_types_exp (str): expected results for the unknown
                cashflow types

        """
        parser = getattr(
            getattr(sys.modules[__name__], platform.lower()),
            'parse_statement')
        (df, unknown_cf_types) = parser(date_range, input_file)
        df_exp = pd.read_csv(
            exp_result_file, index_col=[0, 1, 2])

        # Round both data frames to two digits to avoid minor rounding errors
        # during the comparison
        df = df.round(2)
        df_exp = df_exp.round(2)

        # Reset the index to allow comparing index values/types too
        df.reset_index(inplace=True)
        df_exp.reset_index(inplace=True)
        df_exp.fillna('NaN', inplace=True)

        # Explicitly set the date column to datetime format
        df_exp['Datum'] = pd.to_datetime(df_exp['Datum'])

        # If df is empty, df.equals() will not work since we imported df_exp
        # with non-empty index_cols
        if df.empty:
            self.assertTrue(df_exp.empty)
        else:
            self.assertTrue(df.equals(df_exp))
        self.assertEqual(unknown_cf_types, unknown_cf_types_exp)

    def test_bondora_parser(self):
        """Test parsing Bondora statement"""
        test_name = 'bondora_parser.csv'
        self.run_parser_test(
            'bondora', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    def test_bondora_parser_missing_month(self):
        """
        Test parsing Bondora statement if a month in date_range is missing
        """
        test_name = 'bondora_parser_missing_month.csv'
        self.run_parser_test(
            'bondora', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            self.date_range_missing_month)

    def test_bondora_parser_no_cfs(self):
        """
        Test parsing Bondora statement if there were no cashflows in date_range
        """
        test_name = 'bondora_parser_no_cfs.csv'
        self.run_parser_test(
            'bondora', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            self.date_range_no_cfs)

    def test_dofinance_parser(self):
        """Test parsing DoFinance statement"""
        test_name = 'dofinance_parser'
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        self.run_parser_test(
            'dofinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', dofinance_date_range)

    def test_dofinance_parser_unknown_cf(self):
        """
        Test parsing DoFinance statement if unknown cashflow types are present
        """
        test_name = 'dofinance_parser_unknown_cf'
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        self.run_parser_test(
            'dofinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', dofinance_date_range,
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_dofinance_parser_missing_month(self):
        """
        Test parsing DoFinance statement if a month in date_range is missing
        """
        test_name = 'dofinance_parser_missing_month'
        dofinance_date_range = (date(2018, 5, 1), date(2018, 9, 30))
        self.run_parser_test(
            'dofinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            dofinance_date_range)

    def test_dofinance_parser_no_cfs(self):
        """
        Test parsing DoFinance statement if there were no cashflows in
        date_range
        """
        test_name = 'dofinance_parser_no_cfs'
        self.run_parser_test(
            'dofinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            self.date_range_no_cfs)

    def test_dofinance_parser_wrong_column_names(self):
        """
        Test parsing DoFinance statement if there are unknown column
        names in the statement
        """
        self.assertRaises(
            RuntimeError, dofinance.parse_statement,
            (date(2018, 9, 1), date(2018, 12, 31)),
            INPUT_PREFIX + 'dofinance_parser_wrong_column_names.xlsx')

    def test_estateguru_parser(self):
        """Test parsing Estateguru statement"""
        test_name = 'estateguru_parser.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    def test_estateguru_parser_missing_month(self):
        """
        Test parsing Estateguru statement if a month in date_range is missing
        """
        test_name = 'estateguru_parser_missing_month.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            self.date_range_missing_month)

    def test_estateguru_parser_no_cfs(self):
        """
        Test parsing Estateguru statement if there were no cashflows in
        date_range
        """
        test_name = 'estateguru_parser_no_cfs.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            self.date_range_no_cfs)

    def test_estateguru_parser_unknown_cf(self):
        """
        Test parsing Estateguru statement if unknown cashflow types are present
        """
        test_name = 'estateguru_parser_unknown_cf.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            unknown_cf_types_exp=\
                'Investition(AutoInvestieren), TestCF1, TestCF2')

    def test_grupeer_parser(self):
        """Test parsing Grupeer statement"""
        test_name = 'grupeer_parser'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_grupeer_parser_unknown_cf(self):
        """
        Test parsing Grupeer statement if unknown cashflow types are present
        """
        test_name = 'grupeer_parser_unknown_cf'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='TestCF1, TestCF2')

    def test_grupeer_parser_no_cfs(self):
        """
        Test parsing Grupeer statement if there were no cashflows in date_range
        """
        test_name = 'grupeer_parser_no_cfs'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_grupeer_parser_missing_month(self):
        """
        Test parsing Grupeer statement if a month in date_range is missing
        """
        test_name = 'grupeer_parser_missing_month'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_grupeer_parser_unknown_currency(self):
        """
        Test parsing Grupeer statement if unknown currencies types are present
        """
        test_name = 'grupeer_parser_unknown_currency'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_iuvo_parser(self):
        """Test parsing Iuvo statement"""
        test_name = 'iuvo_parser'
        self.run_parser_test(
            'iuvo', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_iuvo_parser_no_cfs(self):
        """
        Test parsing Iuvo statement if there were no cashflows in date_range
        """
        test_name = 'iuvo_parser_no_cfs'
        self.run_parser_test(
            'iuvo', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_iuvo_parser_missing_month(self):
        """
        Test parsing Iuvo statement if a month in date_range is missing
        """
        test_name = 'iuvo_parser_missing_month'
        self.run_parser_test(
            'iuvo', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_mintos_parser(self):
        """Test parsing Mintos statement"""
        test_name = 'mintos_parser'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_mintos_parser_unknown_cf(self):
        """
        Test parsing Mintos statement if unknown cashflow types are present
        """
        test_name = 'mintos_parser_unknown_cf'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp='Interestincome, TestCF1, TestCF2')

    def test_mintos_parser_no_cfs(self):
        """
        Test parsing Mintos statement if there were no cashflows in date_range
        """
        test_name = 'mintos_parser_no_cfs'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_mintos_parser_missing_month(self):
        """
        Test parsing Mintos statement if a month in date_range is missing
        """
        test_name = 'mintos_parser_missing_month'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_peerberry_parser(self):
        """Test parsing Peerberry statement"""
        test_name = 'peerberry_parser.csv'
        self.run_parser_test(
            'peerberry', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    def test_peerberry_parser_no_cfs(self):
        """
        Test parsing Peerberry statement if there were no cashflows in
        date_range
        """
        test_name = 'peerberry_parser_no_cfs'
        self.run_parser_test(
            'peerberry', INPUT_PREFIX + test_name + '.csv',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_peerberry_parser_missing_month(self):
        """
        Test parsing Peerberry statement if a month in date_range is missing
        """
        test_name = 'peerberry_parser_missing_month'
        self.run_parser_test(
            'peerberry', INPUT_PREFIX + test_name + '.csv',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_robocash_parser(self):
        """Test parsing Robocash statement"""
        test_name = 'robocash_parser'
        self.run_parser_test(
            'robocash', INPUT_PREFIX + test_name + '.xls',
            RESULT_PREFIX + test_name + '.csv')

    def test_robocash_parser_no_cfs(self):
        """
        Test parsing Robocash statement if there were no cashflows in
        date_range
        """
        test_name = 'robocash_parser_no_cfs'
        self.run_parser_test(
            'robocash', INPUT_PREFIX + test_name + '.xls',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_robocash_parser_missing_month(self):
        """
        Test parsing Robocash statement if a month in date_range is missing
        """
        test_name = 'robocash_parser_missing_month'
        self.run_parser_test(
            'robocash', INPUT_PREFIX + test_name + '.xls',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_swaper_parser(self):
        """Test parsing Swaper statement"""
        test_name = 'swaper_parser'
        self.run_parser_test(
            'swaper', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_swaper_parser_no_cfs(self):
        """
        Test parsing Swaper statement if there were no cashflows in date_range
        """
        test_name = 'swaper_parser_no_cfs'
        self.run_parser_test(
            'swaper', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_swaper_parser_missing_month(self):
        """
        Test parsing Swaper statement if a month in date_range is missing
        """
        test_name = 'swaper_parser_missing_month'
        self.run_parser_test(
            'swaper', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_twino_parser(self):
        """Test parsing Twino statement"""
        test_name = 'twino_parser'
        self.run_parser_test(
            'twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_twino_parser_unknown_cf(self):
        """
        Test parsing Twino statement if unknown cashflow types are present
        """
        test_name = 'twino_parser_unknown_cf'
        self.run_parser_test(
            'twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            unknown_cf_types_exp=('TestCF1 PRINCIPAL, TestCF2 INTEREST'))

    def test_twino_parser_wrong_column_names(self):
        """
        Test parsing Twino statement if unknown column names are present in
        the statement
        """
        self.assertRaises(
            RuntimeError, twino.parse_statement,
            (date(2018, 9, 1), date(2018, 12, 31)),
            INPUT_PREFIX + 'twino_parser_wrong_column_names.xlsx')

    def test_twino_parser_no_cfs(self):
        """
        Test parsing Twino statement if there were no cashflows in date_range
        """
        test_name = 'twino_parser_no_cfs'
        self.run_parser_test(
            'twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_no_cfs)

    def test_twino_parser_missing_month(self):
        """
        Test parsing Twino statement if a month in date_range is missing
        """
        test_name = 'twino_parser_missing_month'
        self.run_parser_test(
            'twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv', self.date_range_missing_month)

    def test_show_results(self):
        """Test show_results"""
        list_of_dfs = []

        for platform in PLATFORMS:
            df = p2p_helper.get_df_from_file(
                RESULT_PREFIX + '{0}_parser.csv'.format(
                    platform.lower()))
            df.set_index(['Plattform', 'Datum', 'Währung'], inplace=True)
            list_of_dfs.append(df)

        p2p_parser.show_results(
            list_of_dfs, 'test_show_results.xlsx')

        month_pivot_table = pd.read_excel(
            'test_show_results.xlsx', 'Monatsergebnisse')
        month_pivot_table_exp = pd.read_excel(
            RESULT_PREFIX + 'show_results.xlsx', 'Monatsergebnisse')
        totals_pivot_table = pd.read_excel(
            'test_show_results.xlsx', 'Gesamtergebnis')
        totals_pivot_table_exp = pd.read_excel(
            RESULT_PREFIX + 'show_results.xlsx', 'Gesamtergebnis')

        self.assertTrue(month_pivot_table.equals(month_pivot_table_exp))
        self.assertTrue(totals_pivot_table.equals(totals_pivot_table_exp))


def are_files_equal(
        file1: str, file2: str,
        drop_header: bool = False) -> bool:
    """
    Function to determine if two files are equal.

    Args:
        file1 (str): Name including path of first file
        file2 (str): Name including path of second file

    Keyword Args:
        drop_header: If True the header of the files will be ignored in the
            comparison

    Returns:
        bool: True if the files are equal, False if not or if at least one
        of the files does not exist

    """
    try:
        df1 = p2p_helper.get_df_from_file(file1)
        df2 = p2p_helper.get_df_from_file(file2)
    except RuntimeError:
        return False

    if drop_header:
        df1 = drop_df_header(df1)
        df2 = drop_df_header(df2)

    return df1.equals(df2)


def drop_df_header(df: pd.DataFrame) -> pd.DataFrame:
    """
    Helper function to drop the header of a pandas DataFrame.

    Args:
        df: DataFrame including header

    Returns:
        DataFrame with the header row removed.

    """
    df = df[1:]  # The first row only contains a generic header
    new_header = df.iloc[0] # Get the new first row as header
    df = df[1:] # Remove the first row
    df.columns = new_header # Set the new header

    return df

if __name__ == "__main__":
    unittest.main()
