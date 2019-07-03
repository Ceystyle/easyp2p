# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module implementing Signals for communicating with the GUI."""

from functools import wraps

from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):

    """Class for signal communication between worker classes and GUI."""

    update_progress_bar = pyqtSignal()
    add_progress_text = pyqtSignal(str, bool)
    abort_signal = pyqtSignal()
    end_easyp2p = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.abort = False
        self.abort_signal.connect(self.abort_evaluation)

    def update_progress(self, func):
        """Decorator for updating progress text and progress bar."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if self.abort:
                    raise RuntimeError('Abort by user')
                else:
                    result = func(*args, **kwargs)
            except RuntimeError as err:
                self.add_progress_text.emit(str(err), True)
                raise PlatformFailedError from err
            except RuntimeWarning as err:
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
                self.add_progress_text.emit(str(err), True)
                raise PlatformFailedError from err
            except RuntimeWarning as err:
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
        self.update_progress_bar.connect(other.update_progress_bar)
        self.add_progress_text.connect(other.add_progress_text)
        self.end_easyp2p.connect(other.end_easyp2p)
        other.abort_signal.connect(self.abort_signal)
        self.abort = other.abort

    def disconnect_signals(self) -> None:
        """
        Disconnect signals. Ignore error if they were not connected.
        """
        try:
            self.update_progress_bar.disconnect()
            self.add_progress_text.disconnect()
            self.end_easyp2p.disconnect()
        except TypeError:
            pass

    def abort_evaluation(self):
        """Set the abort flag to True."""
        self.abort = True


class PlatformFailedError(Exception):

    """Will be raised if evaluation of a P2P platform fails."""
