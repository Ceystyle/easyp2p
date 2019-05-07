# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing CredentialsWindow."""

from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox

from easyp2p.ui.Ui_credentials_window import Ui_CredentialsWindow


class CredentialsWindow(QDialog, Ui_CredentialsWindow):
    """Class for getting P2P platform login credentials from the user."""

    def __init__(
            self, platform: str, keyring_exists: bool,
            save_in_keyring: bool = False) -> None:
        """
        Constructor of CredentialsWindow.

        Args:
            platform: Name of the P2P platform.
            keyring_exists: True if a keyring is available, False if not.

        Keyword Args:
            save_in_keyring: If True the save_in_keyring checkbox will be
                checked and disabled.

        """
        super().__init__()
        self.setupUi(self)
        self.platform = platform
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.save_in_keyring = False
        self.label_platform.setText(
            'Bitte Benutzername und Passwort für {0} eingeben:'.format(
                platform))
        if not keyring_exists:
            self.check_box_save_in_keyring.setEnabled(False)
        elif save_in_keyring:
            self.check_box_save_in_keyring.setChecked(True)
            self.check_box_save_in_keyring.setEnabled(False)
            self.save_in_keyring = True

    @pyqtSlot()
    def on_button_box_accepted(self):
        """
        Make sure credentials were entered if user clicks on OK.
        """
        if not self.line_edit_username.text() or \
                not self.line_edit_password.text():
            QMessageBox.warning(
                self, 'Felder nicht ausgefüllt',
                'Bitte Felder für Benutzername und Passwort ausfüllen!')
            return

        self.username = self.line_edit_username.text()
        self.password = self.line_edit_password.text()
        self.save_in_keyring = self.check_box_save_in_keyring.isChecked()
        self.accept()

    def warn_user(self, header, msg):
        """Display a warning message to the user."""
        QMessageBox.warning(self, header, msg)
