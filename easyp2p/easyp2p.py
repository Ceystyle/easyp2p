# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
    easyP2P gets investment results from various P2P platforms.
"""
__author__ = 'Niko Sandschneider'
__copyright__ = 'Copyright (C) 2018-19 Niko Sandschneider'
__license__ = 'MIT'
__version__ = '0.1'

import sys
from PyQt5 import QtWidgets
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
