# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""Module implementing SettingsWindow, the settings window of easyp2p."""
from typing import AbstractSet, Set

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QInputDialog, QMessageBox

import easyp2p.p2p_credentials as p2p_cred
from easyp2p.p2p_settings import Settings
from easyp2p.ui.Ui_settings_window import Ui_SettingsWindow


class SettingsWindow(QDialog, Ui_SettingsWindow):

    """Adjust easyp2p settings and user credentials for the P2P platforms."""

    def __init__(self, platforms: AbstractSet[str], settings: Settings) -> None:
        """
        Constructor of SettingsWindow.

        Args:
            platforms: Set containing the names of all supported P2P platforms
            settings: Settings for easyp2p

        """
        super().__init__()
        self.setupUi(self)

        self.platforms = platforms
        self.settings = settings
        self.saved_platforms: Set[str] = set()
        if p2p_cred.keyring_exists():
            for platform in sorted(self.platforms):
                if p2p_cred.get_password_from_keyring(platform, 'username'):
                    self.list_widget_platforms.addItem(platform)
                    self.saved_platforms.add(platform)
        else:
            self.list_widget_platforms.addItem('Kein Keyring vorhanden!')
            self.push_button_add.setEnabled(False)
            self.push_button_change.setEnabled(False)
            self.push_button_delete.setEnabled(False)
        self.check_box_headless.setChecked(not self.settings.headless)

    @pyqtSlot()
    def on_push_button_add_clicked(self) -> None:
        """Add credentials for a platform to the keyring."""
        not_saved_platforms = {
            platform for platform in self.platforms
            if platform not in self.saved_platforms}

        if not_saved_platforms:
            platform, accepted = QInputDialog.getItem(
                self, 'P2P-Plattform auswählen',
                'Für welche P2P-Plattform sollen Zugangsdaten hinzugefügt '\
                'werden?', sorted(not_saved_platforms), 0, False)
        else:
            QMessageBox.information(
                self, 'Keine weiteren Plattformen verfügbar!',
                ('Es sind bereits Zugangsdaten für alle unterstützten '
                 'Plattformen vorhanden!'))
            return

        if platform and accepted:
            (username, _) = p2p_cred.get_credentials_from_user(
                platform, True)
            if username:
                self.list_widget_platforms.addItem(platform)
                self.saved_platforms.add(platform)

    @pyqtSlot()
    def on_push_button_change_clicked(self) -> None:
        """Change credentials for selected platform in the keyring."""
        platform = self.list_widget_platforms.currentItem().text()
        p2p_cred.get_credentials_from_user(platform, True)

    @pyqtSlot()
    def on_push_button_delete_clicked(self) -> None:
        """Delete credentials for a platform from the keyring."""
        platform = self.list_widget_platforms.currentItem().text()
        msg = QMessageBox.question(
            self, 'Zugangsdaten löschen?',
            'Zugangsdaten für {0} wirklich löschen?'.format(platform))
        if msg == QMessageBox.Yes:
            if not p2p_cred.delete_platform_from_keyring(platform):
                QMessageBox.warning(
                    self, 'Löschen nicht erfolgreich!',
                    ('Leider konnten die {0}-Zugangsdaten nicht gelöscht '
                     'werden!'.format(platform)))
                return
            self.list_widget_platforms.takeItem(
                self.list_widget_platforms.row(
                    self.list_widget_platforms.currentItem()))
            self.saved_platforms.remove(platform)

    @pyqtSlot()
    def on_button_box_accepted(self):
        """Update settings if user clicked OK."""
        self.settings.headless = not self.check_box_headless.isChecked()
        self.accept()
