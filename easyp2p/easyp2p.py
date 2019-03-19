# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
easyp2p.

Package for downloading and presenting investment results for several P2P
lending platforms in a unified way.

"""
import sys
from PyQt5 import QtWidgets
from easyp2p.ui.main_window import MainWindow

name = "easyp2p"
__author__ = 'Niko Sandschneider'
__copyright__ = 'Copyright (C) 2018-19 Niko Sandschneider'
__license__ = 'MIT'
__version__ = '0.0.1'

def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
