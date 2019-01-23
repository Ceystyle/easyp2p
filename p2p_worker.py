# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing WorkerThread."""

from datetime import date
from typing import AbstractSet, Mapping, Tuple

from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QColor

import p2p_parser
import p2p_platforms


class WorkerThread(QThread):

    """
    Worker thread to offload calls to p2p_webdriver, p2p_parser, p2p_results.

    This class is responsible for accessing the P2P platform methods in
    p2p_webdriver and to prepare the results. The main reason for separating
    the calls to p2p_webdriver, p2p_parser and p2p_results from the main thread
    is to keep the GUI responsive while the webdriver is working.

    """

    # Signals for communicating with the MainWindow
    update_progress_bar = pyqtSignal(float)
    update_progress_text = pyqtSignal(str, QColor)

    # Colors for text output
    BLACK = QColor(0, 0, 0)
    RED = QColor(100, 0, 0)

    def __init__(
            self, platforms: AbstractSet[str],
            credentials: Mapping[str, Tuple[str, str]],
            start_date: date, end_date: date, output_file: str,
            parent=None) -> None:
        """
        Constructor.

        Args:
            platforms (set[str]): set containing the names of all selected P2P
                platforms
            credentials (dict[str, tuple[str, str]]): keys are the names of the
                P2P platforms, values are tuples with (username, password)
            start_date (datetime.date): start of date range for which the
                account statements should be generated.
            end_date (datetime.date): end of date range for which the
                account statements should be generated.
            output_file (str): name of the Excel file (including absolute path)
                to which the results should be written.

        Keyword Args:
            parent (QThread): reference to the parent thread

        """
        super(WorkerThread, self).__init__(parent)
        self.platforms = platforms
        self.credentials = credentials
        self.start_date = start_date
        self.end_date = end_date
        self.output_file = output_file
        self.abort = False

    def get_p2p_function(self, platform: str) -> p2p_platforms.OpenSelenium:
        """
        Helper method to get the name of the appropriate webdriver function.

        Args:
            platform (str): name of the P2P platform

        Returns:
            OpenSelenium: p2p_webdriver.open_selenium_* function for handling
                this P2P platform or None if the function cannot be found

        """
        try:
            func = getattr(p2p_platforms, 'open_selenium_'+platform.lower())
        except AttributeError:
            error_message = (
                'Funktion zum Öffnen von {0} konnte nicht gefunden werden. '
                'Ist p2p_webdriver.py vorhanden?'.format(platform))
            self.update_progress_text.emit(error_message, self.RED)
            return None
        else:
            return func

    def get_p2p_parser(self, platform: str) -> p2p_parser.Parser:
        """
        Helper method to get the name of the appropriate parser.

        Args:
            platform (str): name of the P2P platform

        Returns:
            Parser: p2p_parser.* function for parsing this P2P platform or
                None if the function cannot be found

        """
        try:
            parser = getattr(p2p_parser, platform.lower())
        except AttributeError:
            error_message = (
                'Parser für {0} konnte nicht gefunden werden. '
                'Ist p2p_parser.py vorhanden?'.format(platform))
            self.update_progress_text.emit(error_message, self.RED)
            return None
        else:
            return parser

    def ignore_platform(self, platform: str, error_msg: str) -> None:
        """
        Helper method for printing ignore and error message to GUI.

        Args:
            platform (str): name of the P2P platform
            error_msg (str): error message

        """
        self.update_progress_text.emit(error_msg, self.RED)
        self.update_progress_text.emit(
            '{0} wird ignoriert!'.format(platform), self.RED)

    def parse_result(
            self, platform: str, parser: p2p_parser.Parser,
            list_of_dfs: list) -> list:
        """
        Helper method for calling the parser and appending the dataframe list.

        Args:
            platform (str): name of the P2P platform
            parser (p2p_parser.Parser): parser method for parsing results
            list_of_dfs (list(pd.DataFrame)): list of DataFrames, one DataFrame
                for each successfully parsed P2P platform

        Returns:
            list(pd.DataFrame): if successful the provided list_of_dfs with one
                DataFrame appended, if not then the original list_of_dfs is
                returned

        """
        try:
            (df, unknown_cf_types) = parser()
            list_of_dfs.append(df)
        except RuntimeError as err:
            self.ignore_platform(platform, err)
            return list_of_dfs

        if unknown_cf_types:
            warning_msg = (
                '{0}: unbekannter Cashflow-Typ wird im Ergebnis '
                'ignoriert: {1}'.format(platform, unknown_cf_types))
            self.update_progress_text.emit(warning_msg, self.RED)

        return list_of_dfs

    def run_platform(
            self, platform: str, func: p2p_platforms.OpenSelenium) -> bool:
        """
        Helper method for calling the open_selenium_* function.

        Args:
            platform (str): name of the P2P platform
            func (wd.OpenSelenium): function to run

        Returns:
            bool: True if function was run without errors, False otherwise.

        """
        success = False
        if self.credentials[platform] is None:
            self.update_progress_text.emit(
                'Keine Zugangsdaten für {0} vorhanden!'.format(platform),
                self.RED)
            return False

        self.update_progress_text.emit(
            'Start der Auswertung von {0}...'.format(platform), self.BLACK)
        try:
            success = func(
                self.start_date, self.end_date, self.credentials[platform])
        except RuntimeError as err:
            self.ignore_platform(platform, str(err))
            return False
        except RuntimeWarning as warning:
            self.update_progress_text.emit(str(warning), self.RED)
            # Continue anyway

        return success

    def run(self):
        """
        Get and output results from all selected P2P platforms.

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

            success = self.run_platform(platform, func)

            if success:
                if self.abort:
                    return

                progress += step
                self.update_progress_bar.emit(progress)
                self.update_progress_text.emit(
                    '{0} erfolgreich ausgewertet!'.format(platform),
                    self.BLACK)

                parser = self.get_p2p_parser(platform)
                if parser is None:
                    continue

                list_of_dfs = self.parse_result(platform, parser, list_of_dfs)

        if self.abort:
            return

        if not p2p_parser.show_results(
                list_of_dfs, self.start_date, self.end_date, self.output_file):
            self.update_progress_text.emit(
                'Keine Ergebnisse vorhanden', self.RED)

        self.update_progress_bar.emit(100)
