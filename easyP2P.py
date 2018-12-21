# -*- coding: utf-8 -*-

"""
    easyP2P gets investment results from various P2P platforms.

    easyP2P is a Python module with a QT GUI for downloading and processing
    of investment results for various P2P lending platforms. The results are
    combined and presented in a unified way in a single Excel file.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from PyQt5 import QtWidgets
import sys
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
