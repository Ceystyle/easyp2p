# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing WorkerThread."""

from datetime import date
from typing import AbstractSet, Callable, Mapping, Optional, Tuple

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
    abort_easyp2p = pyqtSignal(str)
    update_progress_bar = pyqtSignal()
    add_progress_text = pyqtSignal(str, QColor)

    # Colors for text output
    BLACK = QColor(0, 0, 0)
    RED = QColor(100, 0, 0)

    def __init__(
            self, platforms: AbstractSet[str],
            credentials: Mapping[str, Tuple[str, str]],
            date_range: Tuple[date, date], output_file: str) -> None:
        """
        Constructor of WorkerThread.

        Args:
            platforms: Set containing the names of all selected P2P
                platforms
            credentials: Dictionary containing tuples (username, password) for
                each selected P2P platform
            date_range: Date range (start_date, end_date) for which the
                account statements must be generated
            output_file: Name of the Excel file (including absolute path)
                to which the results will be written

        """
        QThread.__init__(self)
        self.platforms = platforms
        self.credentials = credentials
        self.date_range = date_range
        self.output_file = output_file
        self.abort = False
        self.df_result = pd.DataFrame()

    def get_platform_instance(self, name: str) \
            -> Optional[Callable[[Tuple[date, date]], None]]:
        """
        Helper method to get an instance of the platform class.

        Args:
            name: Name of the P2P platform/module

        Returns:
            Platform class or None if the class cannot be found

        """
        try:
            Platform = getattr(getattr(p2p_platforms, name.lower()), name)
        except AttributeError:
            error_message = (
                'Klasse {0} konnte nicht gefunden werden. Ist {1}.py '
                'vorhanden?'.format(name, name.lower()))
            self.add_progress_text.emit(error_message, self.RED)
            return None
        else:
            return Platform(self.date_range)

    def ignore_platform(self, name: str, error_msg: str) -> None:
        """
        Helper method for printing ignore and error message to GUI.

        Args:
            name: Name of the P2P platform
            error_msg: Error message to print

        """
        self.add_progress_text.emit(error_msg, self.RED)
        self.add_progress_text.emit(
            '{0} wird ignoriert!'.format(name), self.RED)

    def parse_statements(
            self, name: str,
            platform: Callable[[Tuple[date, date]], None]) -> bool:
        """
        Helper method for calling the parser and appending the dataframe list.

        Args:
            name: Name of the P2P platform
            platform_instance: Instance of P2PPlatform class

        Returns:
            True on success, False on failure

        """
        try:
            (df, unknown_cf_types) = platform.parse_statement()
            self.df_result = self.df_result.append(df, sort=True)
        except RuntimeError as err:
            self.ignore_platform(name, str(err))
            return False

        if unknown_cf_types:
            warning_msg = (
                '{0}: unbekannter Cashflow-Typ wird im Ergebnis '
                'ignoriert: {1}'.format(name, unknown_cf_types))
            self.add_progress_text.emit(warning_msg, self.RED)

        return True

    def download_statements(
            self, name: str,
            platform: Callable[[Tuple[date, date]], None]) -> bool:
        """
        Helper method for calling the download_statement functions.

        Args:
            name: Name of the P2P platform
            platform: Instance of P2PPlatform class

        Returns:
            True if download finished without errors, False otherwise

        """
        if self.credentials[name] is None:
            self.add_progress_text.emit(
                'Keine Zugangsdaten für {0} vorhanden!'.format(name),
                self.RED)
            return False

        self.add_progress_text.emit(
            'Start der Auswertung von {0}...'.format(name), self.BLACK)

        try:
            platform.download_statement(self.credentials[name])
        except ModuleNotFoundError as err:
            self.abort_easyp2p.emit(str(err))
        except RuntimeError as err:
            self.ignore_platform(name, str(err))
            return False
        except RuntimeWarning as warning:
            self.add_progress_text.emit(str(warning), self.RED)
            # Continue anyway

        return True

    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file. After
        each finished platform the progress bar is increased.

        """
        for name in self.platforms:

            if self.abort:
                return

            platform = self.get_platform_instance(name)
            if platform is None:
                continue

            if self.download_statements(name, platform):
                if self.abort:
                    return

                if self.parse_statements(name, platform):
                    self.add_progress_text.emit(
                        '{0} erfolgreich ausgewertet!'.format(name), self.BLACK)

            self.update_progress_bar.emit()

        if self.abort:
            return

        if not p2p_parser.show_results(self.df_result, self.output_file):
            self.add_progress_text.emit(
                'Keine Ergebnisse vorhanden', self.RED)
