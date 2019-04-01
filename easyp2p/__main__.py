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

name = "easyp2p" #pylint: disable=invalid-name

def main():
    """Open the main window of easyp2p."""
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow() #pylint: disable=invalid-name
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
