#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module providing error messages common to all supported P2P platforms.
"""

from PyQt5.QtCore import QCoreApplication

_translate = QCoreApplication.translate

CHROME_NOT_FOUND = _translate(
    'P2PChrome', 'Either Chrome or Chromium must be installed to evaluate '
    'this P2P platform!')
CHROME_DRIVER_NOT_FOUND = _translate('P2PChrome', 'ChromeDriver was not found!')


class PlatformErrors:  # pylint: disable=too-many-instance-attributes

    """
    Class PlatformErrors can be instantiated to get access to all platform
    specific translatable error messages.

    """

    def __init__(self, name: str) -> None:
        self.name = name

        self.calendar_date_not_found = _translate(
            'P2PPlatform', f'{name}: could not locate date in calendar!')
        self.invalid_credentials = _translate(
            'P2PPlatform', f'{name}: invalid username or password!')
        self.no_logout_method = _translate(
            'P2PPlatform', f'{name}: no method for logout provided!')
        self.load_login_failed = _translate(
            'P2PPlatform', f'{name}: loading login page failed!')
        self.load_login_timeout = _translate(
            'P2PPlatform', f'{name}: loading login page took too long!')
        self.load_statement_page_failed = _translate(
            'P2PPlatform',
            f'{name}: loading account statement page failed!')
        self.login_failed = _translate(
            'P2PPlatform',
            f'{name}: login was not successful. Are the credentials correct?')
        self.logout_failed = _translate(
            'P2PPlatform', f'{name}: logout failed!')
        self.statement_download_failed = _translate(
            'P2PPlatform',
            f'{name}: downloading account statement failed!')
        self.statement_generation_failed = _translate(
            'P2PPlatform',
            f'{name}: generating account statement failed!')
        self.statement_generation_timeout = _translate(
            'P2PPlatform',
            f'{name}: generating account statement took too long!')
        self.tfa_not_supported = _translate(
            'P2PPlatform',
            f'{name}: two factor authorization is not yet supported in '
            f'easyp2p!')

    @staticmethod
    def download_directory_not_empty(directory: str) -> str:
        """
        This error message is shown if the requested download directory is
        not empty.

        Args:
            directory: Absolute path of the download directory.

        Returns:
            Error message.

        """
        return _translate(
            'P2PPlatform', f'Download directory {directory} is not empty!')

    def unknown_request_method(self, method: str) -> str:
        """
        This error message is shown if an unknown requests method, i.e. not
        'get' or 'post', is requested.

        Args:
            method: Method which was requested.

        Returns:
            Error message.

        """
        return _translate(
            'P2PPlatform', f'{self.name}: unknown request method {method}!')
