#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module implementing P2PSession, a class representing a P2P platform.

This module defines the P2PSession class. It contains code for performing log
in, log out, generating and downloading the account statement. It relies mainly
on functionality provided by the requests Session object.

"""

import logging
from typing import Dict, Mapping, Optional, Sequence

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
            data: Optional[Dict[str, str]] = None) -> requests.Response:
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

        if data is None:
            data = dict()
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
    def download_statement(
            self, url: str, location: str, method: str,
            data: Optional[Mapping[str, str]] = None) -> None:
        """
        Download account statement file.

        Downloads the generated account statement from the provided url. The
        downloaded file will be saved at location.

        Args:
            url: URL for downloading the statement.
            location: Absolute file path where to save the statement.
            method: HTTP method to be used to request the statement file; must
                be either 'get' or 'post'.
            data: Dictionary with data for posting request to the URL.

        Raises:
            RuntimeError: If the download page returns an error status code.

        """
        resp = self._request(url, method, _translate(
            'P2PPlatform',
            f'{self.name}: download of account statement failed!'), data)

        with open(location, 'bw') as file:
            file.write(resp.content)

    def generate_account_statement(
            self, url: str, method: str,
            data: Optional[Mapping[str, str]] = None) -> None:
        """
        Generate account statement.

        Args:
            url: URL for generating the statement.
            method: HTTP method to be used to send the request; must be either
                'get' or 'post'.
            data: Dictionary with data for posting request to the URL.

        """
        self._request(url, method, _translate(
            'P2PPlatform',
            f'{self.name}: account statement generation failed!'), data)

    def _request(
            self, url: str, method: str, error_msg: str,
            data: Optional[Mapping[str, str]] = None) -> requests.Response:
        """
        Helper method to send post or get request to an URL.

        Args:
            url: URL to which to send the request.
            method: HTTP method to be used to request the statement file; must
                be either 'get' or 'post'.
            data: Dictionary with data for posting request to the URL.
            error_msg: Error message which will be shown to the user if the
                request fails.

        Returns:
            Response returned by the URL.

        """
        if method == 'get':
            resp = self.sess.get(url)
        elif method == 'post':
            resp = self.sess.post(url, data=data)
        else:
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: unknown method {method} in download_statement!'))

        if resp.status_code != 200:
            self.logger.debug(
                '%s: returned status code %s', self.name, resp.status_code)
            self.logger.debug(resp.text)
            raise RuntimeError(error_msg)

        return resp

    @signals.watch_errors
    def get_values_from_tag(
            self, url: str, tag: str, names: Sequence[str],
            error_msg: str) -> Dict[str, str]:
        """
        Get the values of HTML tags given in names from page specified by url.
        Return them as a dict with key=name and value=value.

        Args:
            url: URL of the website.
            tag: Tag of the HTML element.
            names: List of tag names for which to get the values.
            error_msg: Error message if extraction of value fails.

        Returns:
            Dictionary with tag names as key and tag values as value.

        Raises:
            RuntimeError: If the website returns an error status code or if
            at least one HTML element cannot be found.
        """
        resp = self.sess.get(url)
        if resp.status_code != 200:
            self.logger.debug(
                '%s: returned status code %s', self.name, resp.status_code)
            self.logger.debug(resp.text)
            raise RuntimeError(error_msg)

        soup = BeautifulSoup(resp.text, 'html.parser')
        data = dict()
        for elem in soup.find_all(tag):
            if elem['name'] in names:
                data[elem['name']] = elem['value']

        if len(names) != len(data.keys()):
            # At least one HTML element has not been found
            self.logger.debug('Elements not found in get_values_from_tag!')
            self.logger.debug('Names: %s', str(names))
            self.logger.debug('Keys: %s', str(data.keys()))
            raise RuntimeError(error_msg)

        return data

    def get_url_from_partial_link(
            self, url: str, partial_link: str, error_msg: str) -> str:
        """
        Load HTML source code of web page with URL url and find and return href
        link which contains text partial_link.

        Args:
            url: URL of website which contains the link.
            partial_link: Partial text for identifying the link.
            error_msg: Error message which should be shown to the user in case
                the page cannot be loaded or the link is not found.

        Returns:
            URL of the link.

        Raises:
            RuntimeError: If the link cannot be found on the page.

        """
        resp = self._request(url, 'get', error_msg)
        soup = BeautifulSoup(resp.text, 'html.parser')
        target = None
        for link in soup.find_all('a', href=True):
            if partial_link in link['href']:
                target = link['href']
        if target is None:
            raise RuntimeError(error_msg)

        return target
