# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module implementing Signals for communicating with the GUI."""

from functools import wraps
import logging

from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):

    """Class for signal communication between worker classes and GUI."""

    update_progress_bar = pyqtSignal()
    add_progress_text = pyqtSignal(str, bool)
    abort_signal = pyqtSignal()
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
                self.logger.exception(
                    'Disconnecting signal %s failed.', str(signal))
            else:
                self.logger.debug('Signal %s disconnected.', str(signal))

    def abort_evaluation(self):
        """Set the abort flag to True."""
        self.logger.debug('Aborting evaluation.')
        self.abort = True


class PlatformFailedError(Exception):

    """Will be raised if evaluation of a P2P platform fails."""
