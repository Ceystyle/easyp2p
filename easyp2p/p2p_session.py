#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module implementing P2PSession, a class representing a P2P platform.

This module defines the P2PSession class. It contains code for performing log
in, log out, generating and downloading the account statement. It relies mainly
on functionality provided by the requests Session object.

"""

import logging
from typing import Dict, Optional

from bs4 import BeautifulSoup
from PyQt5.QtCore import QCoreApplication
import requests

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class P2PSession:
    """
    Representation of P2P session including required methods for interaction.

    Represents a P2P platform and the required methods for login/logout,
    generating and downloading account statements.

    """

    # Signals for communicating with the GUI
    signals = Signals()

    def __init__(
            self, name: str, logout_url: str,
            signals: Optional[Signals]) -> None:
        """
        Constructor of P2PSession class.

        Args:
            name: Name of the P2P platform.
            logout_url: URL of the logout page.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = name
        self.logout_url = logout_url
        self.sess = None
        self.logged_in = False
        if signals:
            self.signals.connect_signals(signals)
        self.logger = logging.getLogger('easyp2p.p2p_session.P2PSession')
        self.logger.debug('%s: created P2PSession instance.', self.name)

    @signals.watch_errors
    def __enter__(self) -> 'P2PSession':
        """
        Start of context management protocol.

        Returns:
            Instance of P2PSession class.

        """
        self.sess = requests.Session()
        self.logger.debug('%s: created context manager.', self.name)
        return self

    @signals.watch_errors
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        End of context management protocol.

        If the context manager finishes the user will be logged out of the
        P2P platform. This ensures that easyp2p cleanly logs out of the website
        even in case of errors.

        Raises:
            RuntimeWarning: If logout is not successful.

        """
        if self.logged_in:
            resp = self.sess.get(self.logout_url)
            if resp.status_code != 200:
                raise RuntimeWarning(_translate(
                    'P2PPlatform', f'{self.name}: logout was not successful!'))

    @signals.update_progress
    def log_into_page(
            self, url: str, name_field: str, password_field: str,
            data: Optional[Dict[str, str]]) -> requests.Response:
        """
        Log into the P2P platform.

        This method performs the login procedure for the P2P website. It gets
        the credentials from the keyring or the user and posts them together
        with provided request data to the platform.

        Args:
            url: Request URL of the login page.
            name_field: Request field name of the username.
            password_field: Request field name of the password.
            data: Payload for login request.

        Raises:
            RuntimeError: If login page returns an error.

        """
        self.logger.debug('%s: logging into website.', self.name)

        credentials = get_credentials(self.name, self.signals)
        data[name_field] = credentials[0]
        data[password_field] = credentials[1]

        resp = self.sess.post(url, data=data)
        if resp.status_code != 200:
            self.logger.debug(
                '%s: returned status code %s', self.name, resp.status_code)
            self.logger.debug(resp.text)
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: login was not successful. Are the credentials '
                f'correct?'))

        self.logged_in = True
        self.logger.debug('%s: successfully logged in.', self.name)

        return resp

    @signals.update_progress
    def download_statement(self, url: str, location: str) -> None:
        """
        Download account statement file.

        Downloads the generated account statement from the provided url. The
        downloaded file will be saved at location.

        Args:
            url: URL for downloading the statement.
            location: Absolute file path where to save the statement.

        Raises:
            RuntimeError: If the download page returns an error status code.

        """
        resp = self.sess.get(url)
        if resp.status_code != 200:
            self.logger.debug(
                '%s: returned status code %s', self.name, resp.status_code)
            self.logger.debug(resp.text)
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: download of account statement failed!'))

        with open(location, 'bw') as file:
            file.write(resp.content)

    @signals.watch_errors
    def get_value_from_tag(
            self, url: str, tag: str, name: str,
            error_msg: str) -> Optional[str]:
        """
        Get the value of a HTML tag from page specified by url.

        Args:
            url: URL of the website.
            tag: Tag of the HTML element.
            name: Name of the tag for which to get the value.
            error_msg: Error message if extraction of value fails.

        Returns:
            Value of the requested HTML element.

        Raises:
            RuntimeError: If the website returns an error status code or if
            the HTML element cannot be found.
        """
        resp = self.sess.get(url)
        if resp.status_code != 200:
            self.logger.debug(
                '%s: returned status code %s', self.name, resp.status_code)
            self.logger.debug(resp.text)
            raise RuntimeError(error_msg)

        soup = BeautifulSoup(resp.text, 'html.parser')
        for elem in soup.find_all(tag):
            if elem['name'] == name:
                return elem['value']

        # The HTML element has not been found
        raise RuntimeError(error_msg)
