from PyQt5 import QtWidgets
import sys
from ui.main_window import MainWindow

if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
