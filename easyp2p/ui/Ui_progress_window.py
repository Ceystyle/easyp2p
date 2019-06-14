# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'progress_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
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
        self.button_box = QtWidgets.QDialogButtonBox(ProgressWindow)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.horizontalLayout.addWidget(self.button_box)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(ProgressWindow)
        self.button_box.accepted.connect(ProgressWindow.accept)
        QtCore.QMetaObject.connectSlotsByName(ProgressWindow)

    def retranslateUi(self, ProgressWindow):
        _translate = QtCore.QCoreApplication.translate
        ProgressWindow.setWindowTitle(_translate("ProgressWindow", "Progress"))


