# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing CredentialsWindow."""

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox

from easyp2p.ui.Ui_credentials_window import Ui_CredentialsWindow


class CredentialsWindow(QDialog, Ui_CredentialsWindow):

    """
    Class for getting P2P platform login credentials from user or keyring.

    CredentialWindow defines a dialog for getting P2P platform credentials
    from a keyring or by user input if the credentials cannot be found in the
    keyring.

    """

    def __init__(self, platform: str, save_in_keyring: bool = False) -> None:
        """
        Constructor of CredentialsWindow.

        Args:
            platform: Name of the P2P platform

        Keyword Args:
            save_in_keyring: If True the save_in_keyring checkbox will be
                checked and disabled

        """
        super().__init__()
        self.setupUi(self)
        self.label_platform.setText('Bitte Benutzername und Passwort für {0} '
            'eingeben:'.format(platform))
        if save_in_keyring:
            self.check_box_save_in_keyring.setChecked(True)
            self.check_box_save_in_keyring.setEnabled(False)

    @pyqtSlot()
    def on_button_box_accepted(self):
        if not self.line_edit_username.text() or \
            not self.line_edit_password.text():
            QMessageBox.warning(
                self, 'Felder nicht ausgefüllt', 'Bitte Felder für '
                'Benutzername und Passwort ausfüllen!')
        else:
            self.accept()
