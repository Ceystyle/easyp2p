# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/niko/workspace/easyp2p/easyp2p/ui/settings_window.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        SettingsWindow.setObjectName("SettingsWindow")
        SettingsWindow.resize(424, 478)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SettingsWindow.sizePolicy().hasHeightForWidth())
        SettingsWindow.setSizePolicy(sizePolicy)
        SettingsWindow.setSizeGripEnabled(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(SettingsWindow)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.list_widget_platforms = QtWidgets.QListWidget(self.groupBox)
        self.list_widget_platforms.setObjectName("list_widget_platforms")
        self.verticalLayout_3.addWidget(self.list_widget_platforms)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.push_button_add = QtWidgets.QPushButton(self.groupBox)
        self.push_button_add.setObjectName("push_button_add")
        self.horizontalLayout.addWidget(self.push_button_add)
        self.push_button_change = QtWidgets.QPushButton(self.groupBox)
        self.push_button_change.setObjectName("push_button_change")
        self.horizontalLayout.addWidget(self.push_button_change)
        self.push_button_delete = QtWidgets.QPushButton(self.groupBox)
        self.push_button_delete.setObjectName("push_button_delete")
        self.horizontalLayout.addWidget(self.push_button_delete)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(SettingsWindow)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SettingsWindow)
        self.buttonBox.accepted.connect(SettingsWindow.accept)
        self.buttonBox.rejected.connect(SettingsWindow.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsWindow)

    def retranslateUi(self, SettingsWindow):
        _translate = QtCore.QCoreApplication.translate
        SettingsWindow.setWindowTitle(_translate("SettingsWindow", "Einstellungen"))
        self.groupBox.setTitle(_translate("SettingsWindow", "Im Keyring gespeicherte Zugangsdaten"))
        self.push_button_add.setText(_translate("SettingsWindow", "Hinzufügen"))
        self.push_button_change.setText(_translate("SettingsWindow", "Ändern"))
        self.push_button_delete.setText(_translate("SettingsWindow", "Löschen"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SettingsWindow = QtWidgets.QDialog()
    ui = Ui_SettingsWindow()
    ui.setupUi(SettingsWindow)
    SettingsWindow.show()
    sys.exit(app.exec_())

