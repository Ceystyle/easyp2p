# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module implementing WorkerThread."""

import logging
import os
import tempfile
from typing import Mapping, Optional, Tuple

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
        self.done = False
        self.df_result = pd.DataFrame()
        self.logger = logging.getLogger('easyp2p.p2p_worker.WorkerThread')

    def get_platform_instance(
            self, name: str, statement_without_suffix: str) -> p2p_platforms:
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
            self.logger.exception('Platform not found')
            raise PlatformFailedError(
                _translate(
                    'WorkerThread',
                    f'{name.lower()}.py could not be found!'))
        else:
            return instance

    def parse_statements(self, name: str, platform: p2p_platforms) -> None:
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
            self.logger.error(err)
            raise PlatformFailedError(str(err))

        if unknown_cf_types:
            warning_msg = _translate(
                'WorkerThread',
                f'{name}: unknown cash flow type will be ignored in result:'
                f'{unknown_cf_types}')
            self.signals.add_progress_text.emit(warning_msg, True)

    def download_statements(self, name: str, platform: p2p_platforms) -> None:
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
            msg = f'Credentials for {name} are not available!'
            self.logger.warning(msg)
            raise PlatformFailedError(_translate('WorkerThread', msg))

        self.signals.add_progress_text.emit(_translate(
            'WorkerThread', f'Starting evaluation of {name}...'), False)

        if name == 'Iuvo' and self.settings.headless:
            # Iuvo is currently not supported in headless ChromeDriver mode
            # because it opens a new window for downloading the statement.
            # ChromeDriver does not allow that due to security reasons.
            self.signals.add_progress_text.emit(_translate(
                    'WorkerThread',
                    'Iuvo is not supported with headless ChromeDriver!'), True)
            self.signals.add_progress_text.emit(_translate(
                'WorkerThread', 'Making ChromeDriver visible!'), True)
            self._download_statement(name, platform, False)
        else:
            self._download_statement(name, platform, self.settings.headless)

    def _download_statement(
            self, name: str, platform: p2p_platforms, headless: bool) -> None:
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

    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file.

        """
        self.logger.info(f'Starting worker for {self.settings.platforms}')
        start_date = self.settings.date_range[0].strftime('%Y%m%d')
        end_date = self.settings.date_range[1].strftime('%Y%m%d')

        for name in self.settings.platforms:
            # Create target directories if they don't exist yet
            target_directory = os.path.join(
                self.settings.directory, name.lower())
            if not os.path.isdir(target_directory):
                try:
                    os.makedirs(target_directory, exist_ok=True)
                except OSError:
                    self.logger.exception('Could not create directory!')
                    self.signals.add_progress_text.emit(
                        _translate(
                            'WorkerThread',
                            f'Could not create directory {target_directory}!'),
                        True)
                    break

            # Set target location of account statement file
            statement_without_suffix = os.path.join(
                target_directory,
                f'{name.lower()}_statement_{start_date}-{end_date}')

            try:
                platform = self.get_platform_instance(
                    name, statement_without_suffix)
                self.download_statements(name, platform)
                self.parse_statements(name, platform)
                self.signals.add_progress_text.emit(
                    _translate(
                        'WorkerThread', f'{name} successfully evaluated!'),
                    False)
            except PlatformFailedError as err:
                self.logger.exception('Evaluation of platform failed.')
                self.signals.add_progress_text.emit(str(err), True)
                self.signals.add_progress_text.emit(
                    _translate('WorkerThread', f'{name} will be ignored!'),
                    True)
                continue

        if not write_results(
                self.df_result, self.settings.output_file,
                self.settings.date_range):
            self.signals.add_progress_text.emit(
                _translate('WorkerThread', 'No results available!'), True)

        self.done = True
        self.signals.update_progress_bar.emit()
