# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing WorkerThread."""

from datetime import date
from typing import AbstractSet, Callable, List, Mapping, Optional, Tuple

import pandas as pd
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QColor

import easyp2p.p2p_parser as p2p_parser
import easyp2p.platforms as p2p_platforms

class WorkerThread(QThread):

    """
    Worker thread to offload calls to p2p_platform and p2p_parser.

    This class is responsible for accessing the P2P platform methods in
    p2p_platform and to prepare the results. The main reason for separating
    the calls from the main thread is to keep the GUI responsive while the
    webdriver is working.

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
            date_range: Tuple[date, date], output_file: str,
            parent: QThread = None) -> None:
        """
        Constructor.

        Args:
            platforms: Set containing the names of all selected P2P
                platforms
            credentials: Dictionary where keys are the names of the
                P2P platforms, values are tuples (username, password)
            date_range: Date range (start_date, end_date) for which the
                account statements must be generated
            output_file: Name of the Excel file (including absolute path)
                to which the results will be written

        Keyword Args:
            parent: Reference to the parent thread

        """
        super(WorkerThread, self).__init__(parent)
        self.platforms = platforms
        self.credentials = credentials
        self.date_range = date_range
        self.output_file = output_file
        self.abort = False

    def get_platform_class(self, platform: str) \
            -> Optional[Callable[[Tuple[date, date], Tuple[str, str]], None]]:
        """
        Helper method to get methods from the platform modules.

        Args:
            platform: Name of the P2P platform/module

        Returns:
            platform class or None if the class cannot be found

        """
        try:
            class_ = getattr(getattr(p2p_platforms, platform.lower()), platform)
        except AttributeError:
            error_message = (
                'Klasse {0} konnte nicht gefunden werden. Ist {1}.py '
                'vorhanden?'.format(platform, platform.lower()))
            self.update_progress_text.emit(error_message, self.RED)
            return None
        else:
            return class_

    def ignore_platform(self, platform: str, error_msg: str) -> None:
        """
        Helper method for printing ignore and error message to GUI.

        Args:
            platform: Name of the P2P platform
            error_msg: Error message to print

        """
        self.update_progress_text.emit(error_msg, self.RED)
        self.update_progress_text.emit(
            '{0} wird ignoriert!'.format(platform), self.RED)

    def parse_result(
            self, platform: str, list_of_dfs: List[pd.DataFrame],
            platform_instance: Callable[[Tuple[date, date]], None]) \
            -> List[pd.DataFrame]:
        """
        Helper method for calling the parser and appending the dataframe list.

        Args:
            platform: Name of the P2P platform
            list_of_dfs: List of DataFrames, one DataFrame for each
                successfully parsed P2P platform
            platform_instance: platform class with parse_statement method

        Returns:
            If successful the provided list_of_dfs with one DataFrame for this
            platform appended, if not successful the original list_of_dfs is
            returned

        """
        try:
            (df, unknown_cf_types) = platform_instance.parse_statement()
            list_of_dfs.append(df)
        except RuntimeError as err:
            self.ignore_platform(platform, str(err))
            return list_of_dfs

        if unknown_cf_types:
            warning_msg = (
                '{0}: unbekannter Cashflow-Typ wird im Ergebnis '
                'ignoriert: {1}'.format(platform, unknown_cf_types))
            self.update_progress_text.emit(warning_msg, self.RED)

        return list_of_dfs

    def run_platform(
            self, platform: str,
            platform_instance: Callable[[Tuple[date, date]], None]) -> bool:
        """
        Helper method for calling the download_statement functions.

        Args:
            platform: Name of the P2P platform
            platform_instance: platform class with download_statement method

        Returns:
            True if download finished without errors, False otherwise

        """
        if self.credentials[platform] is None:
            self.update_progress_text.emit(
                'Keine Zugangsdaten für {0} vorhanden!'.format(platform),
                self.RED)
            return False

        self.update_progress_text.emit(
            'Start der Auswertung von {0}...'.format(platform), self.BLACK)
        try:
            platform_instance.download_statement(self.credentials[platform])
        except RuntimeError as err:
            self.ignore_platform(platform, str(err))
            return False
        except RuntimeWarning as warning:
            self.update_progress_text.emit(str(warning), self.RED)
            # Continue anyway

        return True

    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file. After
        each finished platform the progress bar is increased.

        """
        list_of_dfs: List[pd.DataFrame] = []
        progress = 0.
        # Distribute 95% evenly across all selected platforms
        # The last 5 percent are for preparing the results
        step = 95/len(self.platforms)

        for platform in self.platforms:
            if self.abort:
                return

            class_ = self.get_platform_class(platform)
            if class_ is None:
                continue

            platform_instance = class_(self.date_range)
            success = self.run_platform(platform, platform_instance)

            if success:
                if self.abort:
                    return

                progress += step
                self.update_progress_bar.emit(progress)
                self.update_progress_text.emit(
                    '{0} erfolgreich ausgewertet!'.format(platform),
                    self.BLACK)

                list_of_dfs = self.parse_result(
                    platform, list_of_dfs, platform_instance)

        if self.abort:
            return

        if not p2p_parser.show_results(
                list_of_dfs, self.output_file):
            self.update_progress_text.emit(
                'Keine Ergebnisse vorhanden', self.RED)

        self.update_progress_bar.emit(100)
