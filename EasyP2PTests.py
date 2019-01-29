# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module containing all tests for easyP2P"""

from datetime import date
import sys
from typing import Mapping, Tuple, Union
import unittest

import keyring
import pandas as pd
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest

from ui.main_window import MainWindow
from ui.progress_window import ProgressWindow
import p2p_parser
import p2p_platforms

PLATFORMS = {
    'Bondora': 'csv',
    'DoFinance': 'xlsx',
    'Estateguru': 'csv',
    'Grupeer': 'xlsx',
    'Iuvo': 'csv',
    'Mintos': 'xlsx',
    'PeerBerry': 'csv',
    'Robocash': 'xlsx',
    'Swaper': 'xlsx',
    'Twino': 'xlsx'}
INPUT_PREFIX = 'tests/input/input_test_'
RESULT_PREFIX = 'tests/results/result_test_'

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
        self.form = ProgressWindow()

    def test_defaults(self):
        self.setup_gui()
        self.assertEqual(self.form.progressBar.value(), 0)
        self.assertEqual(self.form.progressText.isReadOnly(), True)
        self.assertEqual(self.form.progressText.toPlainText(), '')
        self.assertEqual(self.form.pushButton_ok.isEnabled(), False)
        self.assertEqual(self.form.pushButton_abort.isEnabled(), True)


class P2PPlatformsTests(unittest.TestCase):
    """Test p2p_platforms"""
    def setUp(self):
        """Initializes the default arguments for p2p_platforms."""
        self.date_range = (date(2018, 9, 1), date(2018, 12, 31))

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

    def test_open_selenium_bondora(self) -> None:
        """Test open_selenium_bondora function"""
        credentials = self.get_credentials_from_keyring('Bondora')
        p2p_platforms.open_selenium_bondora(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            'tests/results/result_test_open_selenium_bondora.csv'))

    def test_open_selenium_bondora_no_cfs(self) -> None:
        """Test open_selenium_bondora when no cashflows exist in date range"""
        credentials = self.get_credentials_from_keyring('Bondora')
        p2p_platforms.open_selenium_bondora(
            (date(2016, 9, 1), date(2016, 12, 31)), credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/bondora_statement.csv',
            'tests/results/result_test_open_selenium_bondora_no_cfs.csv'))

    def test_open_selenium_dofinance(self):
        """Test open_selenium_dofinance function"""
        credentials = self.get_credentials_from_keyring('DoFinance')
        p2p_platforms.open_selenium_dofinance(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/dofinance_statement.xlsx',
            'tests/results/result_test_open_selenium_dofinance.xlsx'))

    def test_open_selenium_estateguru(self):
        """Test open_selenium_estateguru function"""
        credentials = self.get_credentials_from_keyring('Estateguru')
        p2p_platforms.open_selenium_estateguru(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/estateguru_statement.csv',
            'tests/results/result_test_open_selenium_estateguru.csv'))

    def test_open_selenium_grupeer(self):
        """Test open_selenium_grupeer function"""
        credentials = self.get_credentials_from_keyring('Grupeer')
        p2p_platforms.open_selenium_grupeer(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/grupeer_statement.xlsx',
            'tests/results/result_test_open_selenium_grupeer.xlsx'))

    def test_open_selenium_iuvo(self):
        """Test open_selenium_iuvo function"""
        credentials = self.get_credentials_from_keyring('Iuvo')
        p2p_platforms.open_selenium_iuvo(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/iuvo_statement.csv',
            'tests/results/result_test_open_selenium_iuvo.csv'))

    def test_open_selenium_mintos(self):
        """Test open_selenium_mintos function"""
        credentials = self.get_credentials_from_keyring('Mintos')
        p2p_platforms.open_selenium_mintos(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/mintos_statement.xlsx',
            'tests/results/result_test_open_selenium_mintos.xlsx'))

    def test_open_selenium_peerberry(self):
        """Test open_selenium_peerberry function"""
        credentials = self.get_credentials_from_keyring('PeerBerry')
        p2p_platforms.open_selenium_peerberry(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/peerberry_statement.csv',
            'tests/results/result_test_open_selenium_peerberry.csv'))

    def test_open_selenium_robocash(self):
        """Test open_selenium_robocash function"""
        credentials = self.get_credentials_from_keyring('Robocash')
        p2p_platforms.open_selenium_robocash(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/robocash_statement.xlsx',
            'tests/results/result_test_open_selenium_robocash.xlsx'))

    def test_open_selenium_swaper(self):
        """Test open_selenium_swaper function"""
        credentials = self.get_credentials_from_keyring('Swaper')
        p2p_platforms.open_selenium_swaper(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/swaper_statement.xlsx',
            'tests/results/result_test_open_selenium_swaper.xlsx'))

    def test_open_selenium_swaper_no_cfs(self) -> None:
        """Test open_selenium_swaper when no cashflows exist in date range"""
        credentials = self.get_credentials_from_keyring('Swaper')
        self.assertRaises(RuntimeError, p2p_platforms.open_selenium_swaper,
            (date(2016, 12, 1), date(2016, 12, 31)), credentials)

    def test_open_selenium_twino(self):
        """Test open_selenium_twino function"""
        credentials = self.get_credentials_from_keyring('Twino')
        p2p_platforms.open_selenium_twino(self.date_range, credentials)
        self.assertTrue(are_files_equal(
            'p2p_downloads/twino_statement.xlsx',
            'tests/results/result_test_open_selenium_twino.xlsx',
            drop_lines=0))


class P2PParserTests(unittest.TestCase):
    """Test p2p_parser"""

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
        func = getattr(p2p_parser, platform.lower())
        (df, unknown_cf_types) = func(date_range, input_file)
        df_exp = pd.read_csv(
            exp_result_file, index_col=[0, 1, 2])

        # Round both data frames to two digits to avoid minor rounding errors
        # during the comparison
        df = df.round(2)
        df_exp = df_exp.round(2)

        # Reset the index to allow comparing index values/types too
        df.reset_index(inplace=True)
        df_exp.reset_index(inplace=True)

        # Explicitly set the date column to datetime format
        df_exp['Datum'] = pd.to_datetime(df['Datum'])

        # If df is empty, df.equals() will not work since we imported df_exp
        # with non-empty index_cols
        if df.empty:
            self.assertTrue(df_exp.empty)
        else:
            self.assertTrue(df.equals(df_exp))
        self.assertEqual(unknown_cf_types, unknown_cf_types_exp)

    def test_bondora_parser(self):
        test_name = 'bondora_parser.csv'
        self.run_parser_test(
            'bondora', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    def test_bondora_parser_missing_month(self):
        test_name = 'bondora_parser_missing_month.csv'
        self.run_parser_test(
            'bondora', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    def test_bondora_parser_no_cfs(self):
        test_name = 'bondora_parser_no_cfs.csv'
        self.run_parser_test(
            'bondora', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    @unittest.expectedFailure
    def test_dofinance_parser(self):
        test_name = 'dofinance_parser'
        self.run_parser_test(
            'dofinance', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_dofinance_parser_wrong_column_names(self):
        self.assertRaises(
            RuntimeError, p2p_parser.dofinance,
            (date(2018, 9, 1), date(2018, 12, 31)),
            INPUT_PREFIX + 'dofinance_parser_wrong_column_names.xlsx')

    @unittest.expectedFailure
    def test_estateguru_parser(self):
        test_name = 'estateguru_parser.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    @unittest.expectedFailure
    def test_estateguru_parser_unknown_cf(self):
        test_name = 'estateguru_parser_unknown_cf.csv'
        self.run_parser_test(
            'estateguru', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name,
            'Investition(AutoInvestieren), TestCF1, TestCF2')

    @unittest.expectedFailure
    def test_grupeer_parser(self):
        test_name = 'grupeer_parser'
        self.run_parser_test(
            'grupeer', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    @unittest.expectedFailure
    def test_iuvo_parser(self):
        test_name = 'iuvo_parser.csv'
        self.run_parser_test(
            'iuvo', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    @unittest.expectedFailure
    def test_mintos_parser(self):
        test_name = 'mintos_parser'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    @unittest.expectedFailure
    def test_mintos_parser_unknown_cf(self):
        test_name = 'mintos_parser_unknown_cf'
        self.run_parser_test(
            'mintos', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv',
            'Interestincome, TestCF1, TestCF2')

    @unittest.expectedFailure
    def test_peerberry_parser(self):
        test_name = 'peerberry_parser.csv'
        self.run_parser_test(
            'peerberry', INPUT_PREFIX + test_name, RESULT_PREFIX + test_name)

    @unittest.expectedFailure
    def test_robocash_parser(self):
        test_name = 'robocash_parser'
        self.run_parser_test(
            'robocash', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    @unittest.expectedFailure
    def test_swaper_parser(self):
        test_name = 'swaper_parser'
        self.run_parser_test(
            'swaper', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    @unittest.expectedFailure
    def test_twino_parser(self):
        test_name = 'twino_parser'
        self.run_parser_test(
            'twino', INPUT_PREFIX + test_name + '.xlsx',
            RESULT_PREFIX + test_name + '.csv')

    def test_twino_parser_wrong_column_names(self):
        self.assertRaises(
            RuntimeError, p2p_parser.twino,
            (date(2018, 9, 1), date(2018, 12, 31)),
            INPUT_PREFIX + 'twino_parser_wrong_column_names.xlsx')

def are_files_equal(
        file1: str, file2: str,
        drop_lines: Union[int, Mapping[int, int]] = None) -> bool:
    """
    Function to determine if two files are equal.

    Args:
        file1 (str): Name including path of first file
        file2 (str): Name including path of second file

    Keyword Args:
        drop_lines (int or list[int]): lines in the files by row number
            or range which should not be compared

    Returns:
        bool: True if the files are equal, False if not or if at least one
        of the files does not exist

    """
    try:
        df1 = p2p_parser.get_df_from_file(file1)
        df2 = p2p_parser.get_df_from_file(file2)
    except RuntimeError:
        return False

    if drop_lines is not None:
        df1.drop(df1.index[drop_lines])
        df2.drop(df2.index[drop_lines])

    return df1.equals(df2)


if __name__ == "__main__":
    unittest.main()
