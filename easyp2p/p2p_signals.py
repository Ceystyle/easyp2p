# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module implementing Signals for communicating with the GUI."""

from functools import wraps
import logging
from typing import Tuple

from PyQt5.QtCore import QEventLoop, QObject, pyqtSignal, pyqtSlot


class Signals(QObject):

    """Class for signal communication between worker classes and GUI."""

    update_progress_bar = pyqtSignal()
    add_progress_text = pyqtSignal(str, bool)
    abort_signal = pyqtSignal()
    end_easyp2p = pyqtSignal(str, str)
    get_credentials = pyqtSignal(str)
    send_credentials = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.abort = False
        self.abort_signal.connect(self.abort_evaluation)
        self.logger = logging.getLogger('easyp2p.p2p_signals.Signals')
        self.logger.debug('Created Signals instance.')

    def update_progress(self, func):
        """Decorator for updating progress text and progress bar."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if self.abort:
                    raise RuntimeError('Abort by user')

                result = func(*args, **kwargs)
            except RuntimeError as err:
                self.logger.exception('RuntimeError in update_progress')
                self.add_progress_text.emit(str(err), True)
                raise PlatformFailedError from err
            except RuntimeWarning as err:
                self.logger.warning(
                    'RuntimeWarning in update_progress', exc_info=True)
                self.add_progress_text.emit(str(err), True)
                result = None
            finally:
                self.update_progress_bar.emit()
            return result
        return wrapper

    def watch_errors(self, func):
        """Decorator for emitting error messages to the progress window."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except RuntimeError as err:
                self.logger.exception('RuntimeError in watch_errors.')
                self.add_progress_text.emit(str(err), True)
                raise PlatformFailedError from err
            except RuntimeWarning as err:
                self.logger.warning(str(err))
                self.add_progress_text.emit(str(err), True)
                result = None
            return result
        return wrapper

    def connect_signals(self, other: 'Signals') -> None:
        """
        Helper method for connecting signals of different classes.

        Args:
            other: Signals instance of another class.

        """
        self.logger.debug('Connecting signals.')
        self.update_progress_bar.connect(other.update_progress_bar)
        self.add_progress_text.connect(other.add_progress_text)
        self.get_credentials.connect(other.get_credentials)
        other.send_credentials.connect(self.send_credentials)
        self.logger.debug('Connecting signals successful.')

    def disconnect_signals(self) -> None:
        """
        Disconnect signals. Ignore error if they were not connected or if
        disconnecting fails.
        """
        self.logger.debug('Disconnecting signals.')
        for signal in [
                self.add_progress_text, self.get_credentials,
                self.update_progress_bar]:
            try:
                signal.disconnect()
            except TypeError:
                self.logger.exception(f'Disconnecting signal {signal} failed.')
            else:
                self.logger.debug(f'Signal {signal} disconnected.')

    def abort_evaluation(self):
        """Set the abort flag to True."""
        self.logger.debug('Aborting evaluation.')
        self.abort = True


class CredentialReceiver(QObject):
    """Class for getting platform credentials via signals."""

    get_credentials = pyqtSignal(str)
    send_credentials = pyqtSignal(str, str)

    def __init__(self, signals):
        super().__init__()
        self.credentials = None
        self.event_loop = QEventLoop()
        self.get_credentials.connect(signals.get_credentials)
        signals.send_credentials.connect(self.stop_waiting_for_credentials)

    @pyqtSlot(str, str)
    def stop_waiting_for_credentials(
            self, username: str, password: str) -> None:
        """
        Stop the event loop and return to wait_for_credentials.

        Args:
            username: Username of the P2P platform.
            password: Password of the P2P platform.

        """
        self.credentials = (username, password)
        self.event_loop.exit()

    @pyqtSlot(str)
    def wait_for_credentials(self, platform: str) -> Tuple[str, str]:
        """
        Start an event loop to wait until the user entered credentials.

        Args:
            platform: Name of the P2P platform.

        Returns:
            Tuple (username, password) for the P2P platform.

        """
        self.get_credentials.emit(platform)
        self.event_loop = QEventLoop(self)
        self.event_loop.exec()
        return self.credentials


class PlatformFailedError(Exception):

    """Will be raised if evaluation of a P2P platform fails."""
