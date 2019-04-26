# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing CredentialsWindow."""
from typing import Optional, Tuple

import keyring
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


def get_credentials(platform: str) -> Optional[Tuple[str, str]]:
    """
    Get credentials for P2P platform from keyring.

    If a keyring exists, try to get credentials from it. If not or if they
    cannot be found, ask user for credentials.

    Args:
        platform: Name of the P2P platform

    Returns:
        Tuple (username, password) on success, None otherwise

    """
    _ask_for_credentials = False

    if keyring.get_keyring():
        try:
            username = keyring.get_password(platform, 'username')
            password = keyring.get_password(platform, username)
        except TypeError:
            # Either username or password were not found in the keyring
            _ask_for_credentials = True
    else:
        _ask_for_credentials = True

    if _ask_for_credentials:
        (username, password) = get_credentials_from_user(platform)
        if not username or not password:
            return None

    return (username, password)

def save_credentials_in_keyring(
        platform: str, username: str, password: str) -> bool:
    """
    Save credentials for P2P platform in keyring.

    Args:
        platform: Name of P2P platform
        username: Username for P2P platform
        password: Password for P2P platform

    Returns:
        True if credentials were saved successfully, False if not

    """
    if keyring.get_keyring():
        try:
            keyring.set_password(platform, 'username', username)
            keyring.set_password(platform, username, password)
            return True
        except keyring.errors.PasswordSetError:
            return False

    return False

def get_credentials_from_user(
        platform: str, save_in_keyring: bool = False) \
        -> Tuple[Optional[str], Optional[str]]:
    """
    Ask user for P2P platform credentials.

    Args:
        platform: Name of the P2P platform

    Returns:
        Tuple (username, password) on success, (None, None) otherwise

    """
    username, password = None, None
    while not username or not password:
        credentials_window = CredentialsWindow(platform, save_in_keyring)

        if not credentials_window.exec_():
            # User clicked the Cancel button
            return (None, None)

        username = credentials_window.line_edit_username.text()
        password = credentials_window.line_edit_password.text()
        if not username or not password:
            QMessageBox.warning(
                credentials_window, 'Felder nicht ausgefüllt', 'Bitte '
                'Felder für Benutzername und Passwort ausfüllen!')

    if credentials_window.check_box_save_in_keyring.isChecked():
        if not save_credentials_in_keyring(platform, username, password):
            QMessageBox.warning(
                credentials_window, 'Speichern im Keyring fehlgeschlagen!',
                'Speichern des Passworts im Keyring war leider nicht '
                'erfolgreich!')

    return (username, password)
