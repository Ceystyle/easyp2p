# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/niko/workspace/easyP2P/ui/progress_window.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(412, 286)
        Dialog.setSizeGripEnabled(True)
        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(7, 7, 391, 268))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QtWidgets.QProgressBar(self.layoutWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.progressText = QtWidgets.QTextBrowser(self.layoutWidget)
        self.progressText.setObjectName("progressText")
        self.verticalLayout.addWidget(self.progressText)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_OK = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_OK.setEnabled(False)
        self.pushButton_OK.setObjectName("pushButton_OK")
        self.horizontalLayout.addWidget(self.pushButton_OK)
        self.pushButton_abort = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_abort.setObjectName("pushButton_abort")
        self.horizontalLayout.addWidget(self.pushButton_abort)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "easyP2P"))
        self.pushButton_OK.setText(_translate("Dialog", "OK"))
        self.pushButton_abort.setText(_translate("Dialog", "Abbrechen"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

