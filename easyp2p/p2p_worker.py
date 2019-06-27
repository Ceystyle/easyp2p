# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing WorkerThread."""

from datetime import date
import os
from pathlib import Path
import tempfile
from typing import Callable, Mapping, Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QThread, QCoreApplication

from easyp2p.excel_writer import write_results
from easyp2p.p2p_settings import Settings
from easyp2p.p2p_signals import Signals, PlatformFailedError
from easyp2p.p2p_webdriver import P2PWebDriver
import easyp2p.platforms as p2p_platforms

_translate = QCoreApplication.translate


class WorkerThread(QThread):

    """
    Worker thread to offload calls to p2p_platform and p2p_parser.

    This class is responsible for accessing the P2P platform methods in
    p2p_platform and to prepare the results. The main reason for separating
    the calls from the main thread is to keep the GUI responsive while the
    webdriver is working.

    """

    # Signals for communicating with ProgressWindow
    signals = Signals()

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
        super().__init__()
        self.settings = settings
        self.credentials = credentials
        self.signals.abort = False
        self.done = False
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
            instance = platform(
                self.settings.date_range, statement_without_suffix,
                signals=self.signals)
        except AttributeError:
            raise PlatformFailedError(
                _translate('WorkerThread', '{}.py could not be found!').format(
                    name.lower()))
        else:
            return instance

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
            warning_msg = _translate(
                'WorkerThread', '{0}: unknown cash flow type will be ignored '
                'in result: {1}').format(name, unknown_cf_types)
            self.signals.add_progress_text.emit(warning_msg, True)

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
                _translate(
                    'WorkerThread', 'Credentials for {} are not '
                    'available!').format(name))

        self.signals.add_progress_text.emit(
            _translate('WorkerThread', 'Starting evaluation of {}...').format(
                name), False)

        if name == 'Iuvo' and self.settings.headless:
            # Iuvo is currently not supported in headless ChromeDriver mode
            # because it opens a new window for downloading the statement.
            # ChromeDriver does not allow that due to security reasons.
            self.signals.add_progress_text.emit(
                _translate(
                    'WorkerThread',
                    'Iuvo is not supported with headless ChromeDriver!'), True)
            self.signals.add_progress_text.emit(_translate(
                'WorkerThread', 'Making ChromeDriver visible!'), True)
            self._download_statement(name, platform, False)
        else:
            self._download_statement(name, platform, self.settings.headless)

    def _download_statement(
            self, name: str, platform: Callable[[Tuple[date, date]], None],
            headless: bool) -> None:
        """
        Call platform.download_statement.

        Args:
            name: Name of the P2P platform.
            platform: Instance of P2PPlatform class.
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        with tempfile.TemporaryDirectory() as download_directory:
            with P2PWebDriver(
                    download_directory, headless, self.signals) as driver:
                platform.download_statement(driver, self.credentials[name])

    @signals.update_progress
    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file. After
        each finished platform the progress bar is increased.

        """
        for name in self.settings.platforms:
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
                self.parse_statements(name, platform)
                self.signals.add_progress_text.emit(
                    _translate(
                        'WorkerThread', '{} successfully evaluated!').format(
                            name), False)
            except PlatformFailedError:
                self.signals.add_progress_text.emit(
                    _translate('WorkerThread', '{} will be ignored!').format(
                        name), True)
                continue

        if not write_results(
                self.df_result, self.settings.output_file,
                self.settings.date_range):
            self.signals.add_progress_text.emit(
                _translate('WorkerThread', 'No results available!'), True)

        self.done = True
