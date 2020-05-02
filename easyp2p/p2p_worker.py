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

    def get_platform_instance(self, name: str) -> p2p_platforms:
        """
        Helper method to get an instance of the platform class.

        Args:
            name: Name of the P2P platform/module.

        Returns:
            Platform class instance.

        Raises:
            PlatformFailedError: If the platform class cannot be found or the
                download directory cannot be created.

        """
        try:
            platform = getattr(p2p_platforms, name)
            statement_without_suffix = self.get_statement_location(name)
            instance = platform(
                self.settings.date_range, statement_without_suffix,
                signals=self.signals)
        except AttributeError:
            self.logger.exception('Platform not found')
            raise PlatformFailedError(_translate(
                    'WorkerThread',
                    f'{name.lower()}.py could not be found!'))
        except OSError as err:
            self.logger.exception('Could not create directory!')
            raise PlatformFailedError(str(err).strip(), True)
        else:
            return instance

    def parse_statements(self, platform: p2p_platforms) -> None:
        """
        Helper method for calling the parser and appending the dataframe list.

        Args:
            platform: Instance of P2PPlatform class

        Raises:
            PlatformFailedError: If parse_statement method fails.

        """
        try:
            (df, unknown_cf_types) = platform.parse_statement()
            self.df_result = self.df_result.append(df, sort=True)
        except RuntimeError as err:
            self.logger.error(err)
            raise PlatformFailedError(str(err).strip())

        if unknown_cf_types:
            warning_msg = _translate(
                'WorkerThread',
                f'{platform.name}: unknown cash flow type will be ignored in '
                f'result: {unknown_cf_types}')
            self.signals.add_progress_text.emit(warning_msg, True)

    def download_statements(self, platform: p2p_platforms) -> None:
        """
        Helper method for calling the download_statement methods.

        Args:
            platform: Instance of P2PPlatform class.

        Raises:
            PlatformFailedError: If no credentials for platform are available
                or if the download_statement method fails.

        """
        if self.credentials[platform.name] is None:
            msg = f'Credentials for {platform.name} are not available!'
            self.logger.warning(msg)
            raise PlatformFailedError(_translate('WorkerThread', msg))

        self.signals.add_progress_text.emit(_translate(
            'WorkerThread', f'Starting evaluation of {platform.name}...'),
            False)

        if platform.name == 'Iuvo' and self.settings.headless:
            # Iuvo is currently not supported in headless ChromeDriver mode
            # because it opens a new window for downloading the statement.
            # ChromeDriver does not allow that due to security reasons.
            self.signals.add_progress_text.emit(_translate(
                    'WorkerThread',
                    'Iuvo is not supported with headless ChromeDriver!'), True)
            self.signals.add_progress_text.emit(_translate(
                'WorkerThread', 'Making ChromeDriver visible!'), True)
            self._download_statement(platform, False)
        else:
            self._download_statement(platform, self.settings.headless)

    def _download_statement(
            self, platform: p2p_platforms, headless: bool) -> None:
        """
        Call platform.download_statement.

        Args:
            platform: Instance of P2PPlatform class.
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        with tempfile.TemporaryDirectory() as download_directory:
            with P2PWebDriver(
                    download_directory, headless, self.signals) as driver:
                platform.download_statement(
                    driver, self.credentials[platform.name])

    def get_statement_location(self, name: str) -> Optional[str]:
        """
            Create directory for statement download if it does not exist yet and
            return the absolute path of the target file name.

            Args:
                name: Name of the P2P platform.

            Returns:
                Absolute path of the downloaded statement file without suffix.

            Raises:
                OSError: If creation of the directory fails.

        """
        dir_ = os.path.join(self.settings.directory, name.lower())
        if not os.path.isdir(dir_):
            os.makedirs(dir_, exist_ok=True)
        start_date = self.settings.date_range[0].strftime('%Y%m%d')
        end_date = self.settings.date_range[1].strftime('%Y%m%d')

        return os.path.join(
                dir_, f'{name.lower()}_statement_{start_date}-{end_date}')

    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file.

        """
        self.logger.info(f'Starting worker for {self.settings.platforms}')

        for name in self.settings.platforms:
            try:
                platform = self.get_platform_instance(name)
                self.download_statements(platform)
                self.parse_statements(platform)
                self.signals.add_progress_text.emit(
                    _translate(
                        'WorkerThread', f'{name} successfully evaluated!'),
                    False)
            except PlatformFailedError as err:
                self.logger.exception('Evaluation of platform failed.')
                self.signals.add_progress_text.emit(str(err).strip(), True)
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
