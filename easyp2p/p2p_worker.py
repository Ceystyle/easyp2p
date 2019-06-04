# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing WorkerThread."""

from datetime import date
import os
from pathlib import Path
import tempfile
from typing import Callable, Mapping, Optional, Tuple

import pandas as pd
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QColor

from easyp2p.excel_writer import write_results
from easyp2p.p2p_settings import Settings
import easyp2p.platforms as p2p_platforms
from easyp2p.p2p_webdriver import P2PWebDriver, WebDriverNotFound


class WorkerThread(QThread):

    """
    Worker thread to offload calls to p2p_platform and p2p_parser.

    This class is responsible for accessing the P2P platform methods in
    p2p_platform and to prepare the results. The main reason for separating
    the calls from the main thread is to keep the GUI responsive while the
    webdriver is working.

    """

    # Signals for communicating with ProgressWindow
    abort_easyp2p = pyqtSignal(str, str)
    update_progress_bar = pyqtSignal()
    add_progress_text = pyqtSignal(str, QColor)

    # Colors for text output
    BLACK = QColor(0, 0, 0)
    RED = QColor(100, 0, 0)

    def __init__(
            self, settings: Settings,
            credentials: Mapping[str, Optional[Tuple[str, str]]]) -> None:
        """
        Constructor of WorkerThread.

        Args:
            settings: Settings for easyp2p
            credentials: Dictionary containing tuples (username, password) for
                each selected P2P platform

        """
        QThread.__init__(self)
        self.settings = settings
        self.credentials = credentials
        self.abort = False
        self.df_result = pd.DataFrame()

    def get_platform_instance(self, name: str, statement_without_suffix: str) \
            -> Callable[[Tuple[date, date]], None]:
        """
        Helper method to get an instance of the platform class.

        Args:
            name: Name of the P2P platform/module.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.

        Returns:
            Platform class instance.

        Raises:
            PlatformFailedError: If the platform class cannot be found.

        """
        try:
            platform = getattr(p2p_platforms, name)
        except AttributeError:
            raise PlatformFailedError(
                name.lower(), '.py konnte nicht gefunden werden!')
        else:
            return platform(self.settings.date_range, statement_without_suffix)

    def parse_statements(
            self, name: str,
            platform: Callable[[Tuple[date, date]], None]) -> None:
        """
        Helper method for calling the parser and appending the dataframe list.

        Args:
            name: Name of the P2P platform
            platform: Instance of P2PPlatform class

        Raises:
            PlatformFailedError: If parse_statement method fails.

        """
        try:
            (df, unknown_cf_types) = platform.parse_statement()
            self.df_result = self.df_result.append(df, sort=True)
        except RuntimeError as err:
            raise PlatformFailedError(str(err))

        if unknown_cf_types:
            warning_msg = (
                '{0}: unbekannter Cashflow-Typ wird im Ergebnis '
                'ignoriert: {1}'.format(name, unknown_cf_types))
            self.add_progress_text.emit(warning_msg, self.RED)

    def download_statements(
            self, name: str,
            platform: Callable[[Tuple[date, date]], None]) -> None:
        """
        Helper method for calling the download_statement methods.

        Args:
            name: Name of the P2P platform.
            platform: Instance of P2PPlatform class.

        Raises:
            PlatformFailedError: If no credentials for platform are available
                or if the download_statement method fails.

        """
        if self.credentials[name] is None:
            raise PlatformFailedError(
                'Keine Zugangsdaten für {0} vorhanden!'.format(name))

        self.add_progress_text.emit(
            'Start der Auswertung von {0}...'.format(name), self.BLACK)

        try:
            if name == 'Iuvo' and self.settings.headless:
                # Iuvo is currently not supported in headless Chromedriver mode
                # because it opens a new window for downloading the statement.
                # Chromedriver does not allow that due to security reasons.
                self.add_progress_text.emit(
                    'Iuvo wird nicht mit unsichtbarem Chromedriver '
                    'unterstützt!', self.RED)
                self.add_progress_text.emit(
                    'Mache Chromedriver sichtbar!', self.RED)
                with tempfile.TemporaryDirectory() as download_directory:
                    with P2PWebDriver(download_directory, False) as driver:
                        platform.download_statement(
                            driver, self.credentials[name])
            else:
                with tempfile.TemporaryDirectory() as download_directory:
                    with P2PWebDriver(
                            download_directory,
                            self.settings.headless) as driver:
                        platform.download_statement(
                            driver, self.credentials[name])
        except WebDriverNotFound as err:
            self.abort_easyp2p.emit(str(err), 'ChromeDriver not found!')
            self.abort = True
            return
        except RuntimeError as err:
            raise PlatformFailedError(str(err))
        except RuntimeWarning as warning:
            self.add_progress_text.emit(str(warning), self.RED)
            # Continue anyway

    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file. After
        each finished platform the progress bar is increased.

        """
        for name in self.settings.platforms:

            if self.abort:
                return

            # Set target location of account statement file
            statement_without_suffix = os.path.join(
                Path.home(), '.easyp2p', name.lower(),
                '{0}_statement_{1}-{2}'.format(
                    name.lower(),
                    self.settings.date_range[0].strftime('%Y%m%d'),
                    self.settings.date_range[1].strftime('%Y%m%d')))

            try:
                platform = self.get_platform_instance(
                    name, statement_without_suffix)

                self.download_statements(name, platform)

                if self.abort:
                    return

                self.parse_statements(name, platform)
                self.add_progress_text.emit(
                    '{0} erfolgreich ausgewertet!'.format(name), self.BLACK)
                self.update_progress_bar.emit()
            except PlatformFailedError as err:
                self.add_progress_text.emit(str(err), self.RED)
                self.add_progress_text.emit(
                    '{0} wird ignoriert!'.format(name), self.RED)
                self.update_progress_bar.emit()
                continue

        if self.abort:
            return

        if not write_results(
                self.df_result, self.settings.output_file,
                self.settings.date_range):
            self.add_progress_text.emit(
                'Keine Ergebnisse vorhanden', self.RED)


class PlatformFailedError(BaseException):

    """Will be raised if evaluation of a P2P platform fails."""
