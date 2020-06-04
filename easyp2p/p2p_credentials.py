# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module for getting and saving credentials in the system keyring / from the user.

"""
from typing import Optional, Tuple

import keyring
from keyring.errors import PasswordDeleteError
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal, QEventLoop, pyqtSlot

from easyp2p.p2p_signals import Signals
from easyp2p.ui.credentials_window import CredentialsWindow

_translate = QCoreApplication.translate


def keyring_exists() -> bool:
    """
    Check if there is a keyring available.

    Returns:
        True if a keyring is found, False if not

    """
    return keyring.get_keyring()


def get_credentials_from_keyring(platform):
    """
    Try to get credentials for platform from keyring.

    Args:
        platform: Name of the P2P platform

    Returns:
        Tuple (username, password) or None if credentials were not found in the
        keyring.

    """
    username, password = None, None

    if keyring.get_keyring():
        username = keyring.get_password(platform, 'username')
        if username is not None:
            password = keyring.get_password(platform, username)

    if username is None or password is None:
        return None

    return username, password


def get_credentials_from_user(
        platform: str, save_in_keyring: bool = False) \
        -> Tuple[Optional[str], Optional[str]]:
    """
    Ask user for P2P platform credentials.

    Args:
        platform: Name of the P2P platform
        save_in_keyring: If True the save_in_keyring checkbox will be
            checked and disabled. Default is False.

    Returns:
        Tuple (username, password)

    """
    cred_window = CredentialsWindow(
        platform, keyring.get_keyring(), save_in_keyring)
    cred_window.exec_()

    if cred_window.save_in_keyring:
        if not save_platform_in_keyring(
                platform, cred_window.username, cred_window.password):
            cred_window.warn_user(
                _translate('p2p_credentials', 'Saving in keyring failed!'),
                _translate(
                    'p2p_credentials', 'Saving password in keyring was not '
                    'successful!'))

    return cred_window.username, cred_window.password


def get_credentials(platform: str, signals: Signals) -> Tuple[str, str]:
    """
    Helper function to get credentials for platform from keyring or from user,
    if they are not available in the keyring.

    Args:
        platform: Platform for which to get credentials.
        signals: Signals for communicating with the GUI.

    Returns:
        Tuple (username, password) for platform

    Raises:
        RuntimeError: If no credentials were provided by the user.

    """
    credentials = get_credentials_from_keyring(platform)
    if credentials is None:
        credential_receiver = CredentialReceiver(signals)
        credentials = credential_receiver.wait_for_credentials(platform)

    if credentials[0] == '' or credentials[1] == '':
        raise RuntimeError(_translate(
            'p2p_credentials',
            f'No credentials for {platform} provided! Aborting!'))

    return credentials


def get_password_from_keyring(platform: str, username: str) -> Optional[str]:
    """
    Get password for platform:username from keyring.

    Args:
        platform: Name of the P2P platform
        username: Username for which to get the password

    Returns:
        Password or None if no password was found for username

    """
    return keyring.get_password(platform, username)


def delete_platform_from_keyring(platform: str) -> bool:
    """
    Delete credentials for platform from keyring.

    Args:
        platform: Name of the P2P platform

    Returns:
        True on success, False on failure

    Raises:
        RuntimeError: If 'username' for platform cannot be found in the keyring

    """
    try:
        username = keyring.get_password(platform, 'username')
        if not username:
            raise RuntimeError(
                _translate(
                    'p2p_credentials', f'{platform} was not found in keyring!'))
        keyring.delete_password(platform, username)
        keyring.delete_password(platform, 'username')
    except PasswordDeleteError:
        return False
    return True


def save_platform_in_keyring(
        platform: str, username: str, password: str) -> bool:
    """
    Save credentials for platform in keyring.

    Args:
        platform: Name of the P2P platform
        username: Username for platform
        password: Password for platform

    Returns:
        True on success, False on failure

    Raises:
        RuntimeError: If username == 'username'

    """
    # We use 'username' to save the user name of the platform, thus it cannot be
    # used as a "normal" user name. This is only a hypothetical problem since
    # P2P platforms use email addresses as user names
    if username == 'username':
        raise RuntimeError(
            _translate(
                'p2p_credentials', 'User name "username" is not allowed!'))

    try:
        keyring.set_password(platform, 'username', username)
        keyring.set_password(platform, username, password)
    except keyring.errors.PasswordSetError:
        return False
    return True


class CredentialReceiver(QObject):
    """Class for getting platform credentials via signals."""

    get_credentials = pyqtSignal(str)
    send_credentials = pyqtSignal(str, str)

    def __init__(self, signals):
        super().__init__()
        self.credentials = None
        self.event_loop = QEventLoop()
        self.get_credentials.connect(signals.get_credentials)
        signals.send_credentials.connect(self.stop_waiting_for_credentials)

    @pyqtSlot(str, str)
    def stop_waiting_for_credentials(
            self, username: str, password: str) -> None:
        """
        Stop the event loop and return to wait_for_credentials.

        Args:
            username: Username of the P2P platform.
            password: Password of the P2P platform.

        """
        self.credentials = (username, password)
        self.event_loop.exit()

    @pyqtSlot(str)
    def wait_for_credentials(self, platform: str) -> Tuple[str, str]:
        """
        Start an event loop to wait until the user entered credentials.

        Args:
            platform: Name of the P2P platform.

        Returns:
            Tuple (username, password) for the P2P platform.

        """
        self.get_credentials.emit(platform)
        self.event_loop = QEventLoop(self)
        self.event_loop.exec()
        return self.credentials
