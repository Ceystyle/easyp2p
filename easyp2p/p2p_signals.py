from functools import wraps

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor

# Colors for text output
BLACK = QColor(0, 0, 0)
RED = QColor(100, 0, 0)


class Signals(QObject):

    """Class for signal communication between worker classes and GUI."""

    update_progress_bar = pyqtSignal()
    add_progress_text = pyqtSignal(str, QColor)

    def update_progress(self, func):
        """Decorator for emitting signals to the progress window."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except RuntimeError as err:
                self.add_progress_text.emit(str(err), RED)
                raise PlatformFailedError from err
            except RuntimeWarning as err:
                self.add_progress_text.emit(str(err), RED)
            finally:
                self.update_progress_bar.emit()
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


class PlatformFailedError(Exception):

    """Will be raised if evaluation of a P2P platform fails."""
