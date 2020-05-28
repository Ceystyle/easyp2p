# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module implementing WorkerThread."""

import logging
import os
from typing import Optional

import pandas as pd
from PyQt5.QtCore import QCoreApplication, QThread

from easyp2p.excel_writer import write_results
from easyp2p.p2p_credentials import get_credentials_from_user
from easyp2p.p2p_settings import Settings
from easyp2p.p2p_signals import Signals, PlatformFailedError
import easyp2p.platforms as p2p_platforms

_translate = QCoreApplication.translate


class WorkerThread(QThread):
    """
    Worker thread to offload calls to p2p_platform and p2p_parser.

    This class is responsible for accessing the P2P platform methods in
    p2p_platform and to prepare the results. The main reason for separating
    the calls from the main thread is to keep the GUI responsive while the
    platform is being evaluated.

    """

    # Signals for communicating with ProgressWindow
    signals = Signals()

    def __init__(self, settings: Settings) -> None:
        """
        Constructor of WorkerThread.

        Args:
            settings: Settings for easyp2p.

        """
        super().__init__()
        self.logger = logging.getLogger('easyp2p.p2p_worker.WorkerThread')
        self.settings = settings
        self.signals.get_credentials.connect(self.get_credentials)
        self.done = False
        self.df_result = pd.DataFrame()

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

    def evaluate_platform(self, name: str) -> pd.DataFrame:
        """
        Download and parse the account statement for given platform. Warn the
        user if there were unknown cash flow types.

        Args:
            name: Name of the P2P platform to evaluate.

        Returns:
            Parsed account statement as a data frame.

        """
        platform = self.get_platform_instance(name)
        self.signals.add_progress_text.emit(_translate(
            'WorkerThread',
            f'Starting evaluation of {platform.name}...'), False)

        # Distinguish platforms that use Selenium for evaluation
        if name in ['Iuvo', 'Mintos', 'Grupeer', 'Swaper']:
            platform.download_statement(self.settings.headless)
        else:
            platform.download_statement()
        (df, unknown_cf_types) = platform.parse_statement()

        if unknown_cf_types:
            warning_msg = _translate(
                'WorkerThread',
                f'{name}: unknown cash flow type will be ignored in '
                f'result: {unknown_cf_types}')
            self.signals.add_progress_text.emit(warning_msg, True)

        self.signals.add_progress_text.emit(
            _translate(
                'WorkerThread', f'{name} successfully evaluated!'), False)

        return df

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

    def get_credentials(self, platform: str) -> None:
        """
        Get credentials from user and emit them via a pyqtSignal to the
        CredentialReceiver object.

        Args:
            platform: Name of the P2P platform.

        """
        username, password = get_credentials_from_user(platform)
        self.signals.send_credentials.emit(username, password)

    def run(self) -> None:
        """
        Get and output results from all selected P2P platforms.

        Iterates over all selected P2P platforms, downloads the account
        statements, parses them and writes the results to an Excel file.

        """
        self.logger.info('%s: starting worker.', self.settings.platforms)

        for name in self.settings.platforms:
            try:
                df = self.evaluate_platform(name)
                self.df_result = self.df_result.append(df, sort=True)
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
