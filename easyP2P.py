"""easyP2P
    :platform: Linux
    :synopsis: easyP2P is a Python module for collecting and processing of investment results for various P2P lending platforms

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from PyQt5 import QtWidgets
import sys
from ui.main_window import MainWindow

if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
