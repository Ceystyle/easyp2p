# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Application for downloading and presenting investment results for
people-to-people (P2P) lending platforms.

"""
import sys
from PyQt5 import QtWidgets

from easyp2p.ui.main_window import MainWindow

name = "easyp2p"  # pylint: disable=invalid-name


def main():
    """Open the main window of easyp2p."""
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()  # pylint: disable=invalid-name
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
