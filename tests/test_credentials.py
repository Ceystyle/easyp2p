# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module containing all tests for p2p_credentials."""

import unittest.mock

from keyring.errors import PasswordDeleteError

from easyp2p.p2p_credentials import (
    keyring_exists, get_credentials, get_credentials_from_user,
    get_password_from_keyring, delete_platform_from_keyring,
    save_platform_in_keyring)


@unittest.mock.patch('easyp2p.p2p_credentials.keyring')
class CredentialsTests(unittest.TestCase):

    """Test p2p_credentials."""

    def test_keyring_exists_with_keyring(self, mock_keyring):
        """Test keyring_exists when a keyring is available."""
        mock_keyring.get_keyring.return_value = True
        self.assertTrue(keyring_exists())

    def test_keyring_exists_without_keyring(self, mock_keyring):
        """Test keyring_exists when a keyring is not available."""
        mock_keyring.get_keyring.return_value = False
        self.assertFalse(keyring_exists())

    def test_get_password_from_keyring_if_exists(self, mock_keyring):
        """Test get_password_from_keyring if it exists."""
        mock_keyring.get_password.return_value = 'TestPass'
        self.assertEqual(
            get_password_from_keyring('TestPass', 'TestUser'), 'TestPass')

    def test_get_password_from_keyring_if_not_exists(self, mock_keyring):
        """Test get_password_from_keyring if it does not exists."""
        mock_keyring.get_password.return_value = None
        self.assertEqual(
            get_password_from_keyring('TestPass', 'TestUser'), None)

    def test_save_platform_in_keyring(self, mock_keyring):
        """Test save_platform_in_keyring."""
        self.assertTrue(save_platform_in_keyring(
            'TestPlatform', 'TestUser', 'TestPass'))
        expected_calls = [
            unittest.mock.call('TestPlatform', 'username', 'TestUser'),
            unittest.mock.call('TestPlatform', 'TestUser', 'TestPass')]
        self.assertEqual(
            mock_keyring.set_password.call_args_list, expected_calls)

    def test_save_platform_in_keyring_username_equals_username(
            self, mock_keyring):
        """Test save_platform_in_keyring when username=='username'."""
        self.assertRaises(RuntimeError, save_platform_in_keyring,
            'TestPlatform', 'username', 'TestPass')
        self.assertFalse(mock_keyring.set_password.called)

    def test_delete_platform_from_keyring_if_exists(self, mock_keyring):
        """Test delete_platform_from_keyring if platform exists in keyring."""
        mock_keyring.get_password.return_value = 'TestUser'
        self.assertTrue(delete_platform_from_keyring('TestPlatform'))
        expected_calls = [
            unittest.mock.call('TestPlatform', 'TestUser'),
            unittest.mock.call('TestPlatform', 'username')]
        self.assertEqual(
            mock_keyring.delete_password.call_args_list, expected_calls)

    def test_delete_platform_from_keyring_if_not_exists(self, mock_keyring):
        """
        Test delete_platform_from_keyring if platform does not exist in keyring.
        """
        mock_keyring.get_password.return_value = None
        self.assertRaises(
            RuntimeError, delete_platform_from_keyring, 'TestPlatform')

    def test_delete_platform_from_keyring_password_delete_error(
            self, mock_keyring):
        """
        Test delete_platform_from_keyring if PasswordDeleteError is raised.
        """
        mock_keyring.get_password.return_value = 'TestUser'
        mock_keyring.delete_password = unittest.mock.Mock(
            side_effect=PasswordDeleteError)
        self.assertFalse(delete_platform_from_keyring('TestPlatform'))

    @unittest.mock.patch('easyp2p.p2p_credentials.CredentialsWindow')
    def test_get_credentials_from_user_no_save_in_keyring(
            self, mock_cred_window, mock_keyring):
        """Test getting credentials from the user without saving in keyring."""
        mock_cw = mock_cred_window('TestPlatform', True, False)
        mock_cw.username = 'TestUser'
        mock_cw.password = 'TestPass'
        mock_cw.save_in_keyring = False
        (username, password) = get_credentials_from_user('TestPlatform', False)
        self.assertEqual(username, 'TestUser')
        self.assertEqual(password, 'TestPass')

    @unittest.mock.patch('easyp2p.p2p_credentials.CredentialsWindow')
    @unittest.mock.patch('easyp2p.p2p_credentials.save_platform_in_keyring')
    def test_get_credentials_from_user_save_in_keyring(
            self, mock_save_in_keyring, mock_cred_window, mock_keyring):
        """Test getting credentials from the user with save in keyring."""
        mock_cw = mock_cred_window('TestPlatform', True, False)
        mock_cw.username = 'TestUser'
        mock_cw.password = 'TestPass'
        mock_cw.save_in_keyring = True
        (username, password) = get_credentials_from_user('TestPlatform', False)
        self.assertEqual(username, 'TestUser')
        self.assertEqual(password, 'TestPass')
        mock_save_in_keyring.assert_called_once_with(
            'TestPlatform', 'TestUser', 'TestPass')

    @unittest.mock.patch('easyp2p.p2p_credentials.CredentialsWindow')
    @unittest.mock.patch('easyp2p.p2p_credentials.save_platform_in_keyring')
    def test_get_credentials_from_user_save_in_keyring_fails(
            self, mock_save_in_keyring, mock_cred_window, mock_keyring):
        """
        Test getting credentials from the user with failed save in keyring.
        """
        mock_cw = mock_cred_window('TestPlatform', True, False)
        mock_cw.username = 'TestUser'
        mock_cw.password = 'TestPass'
        mock_cw.save_in_keyring = True
        mock_save_in_keyring.return_value = False
        (username, password) = get_credentials_from_user('TestPlatform', False)
        self.assertEqual(username, 'TestUser')
        self.assertEqual(password, 'TestPass')
        mock_cw.warn_user.assert_called_once_with(
            'Saving in keyring failed!',
            'Saving password in keyring was not successful!')

    def test_get_credentials_if_in_keyring(self, mock_keyring):
        """Get credentials which exist in the keyring."""
        mock_keyring.get_keyring.return_value = True
        mock_keyring.get_password.side_effect = ['TestUser', 'TestPass']
        credentials = get_credentials('TestPlatform')
        self.assertEqual(credentials[0], 'TestUser')
        self.assertEqual(credentials[1], 'TestPass')

    @unittest.mock.patch('easyp2p.p2p_credentials.get_credentials_from_user')
    def test_get_credentials_if_not_in_keyring(
            self, mock_user_credentials, mock_keyring):
        """Get credentials which do not exist in the keyring."""
        mock_keyring.get_keyring.return_value = True
        mock_keyring.get_password.return_value = None
        mock_user_credentials.return_value = ('TestUser', 'TestPass')
        credentials = get_credentials('TestPlatform')
        self.assertEqual(credentials[0], 'TestUser')
        self.assertEqual(credentials[1], 'TestPass')

    @unittest.mock.patch('easyp2p.p2p_credentials.get_credentials_from_user')
    def test_get_credentials_if_not_in_keyring_cancel(
            self, mock_user_credentials, mock_keyring):
        """Get credentials which are not in the keyring and user cancels."""
        mock_keyring.get_keyring.return_value = True
        mock_keyring.get_password.return_value = None
        mock_user_credentials.return_value = (None, None)
        credentials = get_credentials('TestPlatform')
        print(credentials)
        self.assertEqual(credentials, None)

    @unittest.mock.patch('easyp2p.p2p_credentials.get_credentials_from_user')
    def test_get_credentials_if_no_keyring_exists(
            self, mock_user_credentials, mock_keyring):
        """Get credentials when no keyring exists."""
        mock_keyring.get_keyring.return_value = False
        mock_user_credentials.return_value = ('TestUser', 'TestPass')
        credentials = get_credentials('TestPlatform')
        self.assertEqual(credentials[0], 'TestUser')
        self.assertEqual(credentials[1], 'TestPass')

    @unittest.mock.patch('easyp2p.p2p_credentials.get_credentials_from_user')
    def test_get_credentials_if_no_keyring_exists_user_cancels(
            self, mock_user_credentials, mock_keyring):
        """Get credentials when no keyring exists and user cancels dialog."""
        mock_keyring.get_keyring.return_value = False
        mock_user_credentials.return_value = (None, None)
        credentials = get_credentials('TestPlatform')
        self.assertEqual(credentials, None)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestLoader().loadTestsFromTestCase(CredentialsTests)
    result = runner.run(suite)
