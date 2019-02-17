# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/niko/workspace/easyP2P/ui/credentials_window.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CredentialsWindow(object):
    def setupUi(self, CredentialsWindow):
        CredentialsWindow.setObjectName("CredentialsWindow")
        CredentialsWindow.resize(379, 178)
        CredentialsWindow.setSizeGripEnabled(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(CredentialsWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_platform = QtWidgets.QLabel(CredentialsWindow)
        self.label_platform.setWordWrap(True)
        self.label_platform.setObjectName("label_platform")
        self.verticalLayout_3.addWidget(self.label_platform)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.lineEdit_username = QtWidgets.QLineEdit(CredentialsWindow)
        self.lineEdit_username.setText("")
        self.lineEdit_username.setObjectName("lineEdit_username")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_username)
        self.label_username = QtWidgets.QLabel(CredentialsWindow)
        self.label_username.setObjectName("label_username")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_username)
        self.label_password = QtWidgets.QLabel(CredentialsWindow)
        self.label_password.setObjectName("label_password")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_password)
        self.lineEdit_password = QtWidgets.QLineEdit(CredentialsWindow)
        self.lineEdit_password.setText("")
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_password.setObjectName("lineEdit_password")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_password)
        self.verticalLayout_3.addLayout(self.formLayout)
        self.checkBox_save_in_keyring = QtWidgets.QCheckBox(CredentialsWindow)
        self.checkBox_save_in_keyring.setObjectName("checkBox_save_in_keyring")
        self.verticalLayout_3.addWidget(self.checkBox_save_in_keyring)
        self.buttonBox = QtWidgets.QDialogButtonBox(CredentialsWindow)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.retranslateUi(CredentialsWindow)
        QtCore.QMetaObject.connectSlotsByName(CredentialsWindow)

    def retranslateUi(self, CredentialsWindow):
        _translate = QtCore.QCoreApplication.translate
        CredentialsWindow.setWindowTitle(_translate("CredentialsWindow", "Bitte Benutzername und Passwort eingeben!"))
        self.label_platform.setText(_translate("CredentialsWindow", "Bitte geben Sie Benutzername und Passwort für $platform ein:"))
        self.label_username.setText(_translate("CredentialsWindow", "Benutzername"))
        self.label_password.setText(_translate("CredentialsWindow", "Passwort"))
        self.checkBox_save_in_keyring.setText(_translate("CredentialsWindow", "Im Keyring speichern (empfohlen)"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CredentialsWindow = QtWidgets.QDialog()
    ui = Ui_CredentialsWindow()
    ui.setupUi(CredentialsWindow)
    CredentialsWindow.show()
    sys.exit(app.exec_())

