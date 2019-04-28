# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/niko/workspace/easyp2p/easyp2p/ui/progress_window.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ProgressWindow(object):
    def setupUi(self, ProgressWindow):
        ProgressWindow.setObjectName("ProgressWindow")
        ProgressWindow.resize(412, 286)
        ProgressWindow.setSizeGripEnabled(True)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(ProgressWindow)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.progress_bar = QtWidgets.QProgressBar(ProgressWindow)
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setObjectName("progress_bar")
        self.verticalLayout.addWidget(self.progress_bar)
        self.progress_text = QtWidgets.QTextBrowser(ProgressWindow)
        self.progress_text.setObjectName("progress_text")
        self.verticalLayout.addWidget(self.progress_text)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.push_button_ok = QtWidgets.QPushButton(ProgressWindow)
        self.push_button_ok.setEnabled(False)
        self.push_button_ok.setObjectName("push_button_ok")
        self.horizontalLayout.addWidget(self.push_button_ok)
        self.push_button_abort = QtWidgets.QPushButton(ProgressWindow)
        self.push_button_abort.setObjectName("push_button_abort")
        self.horizontalLayout.addWidget(self.push_button_abort)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(ProgressWindow)
        self.push_button_ok.clicked.connect(ProgressWindow.accept)
        QtCore.QMetaObject.connectSlotsByName(ProgressWindow)

    def retranslateUi(self, ProgressWindow):
        _translate = QtCore.QCoreApplication.translate
        ProgressWindow.setWindowTitle(_translate("ProgressWindow", "easyP2P"))
        self.push_button_ok.setText(_translate("ProgressWindow", "OK"))
        self.push_button_abort.setText(_translate("ProgressWindow", "Abbrechen"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ProgressWindow = QtWidgets.QDialog()
    ui = Ui_ProgressWindow()
    ui.setupUi(ProgressWindow)
    ProgressWindow.show()
    sys.exit(app.exec_())

