# -*- coding: utf-8 -*-
""" Test for the '/auth' API-endpoint """

from .base import MyApiTestCase
from privacyidea.lib.config import set_privacyidea_config
import mock


class AuthApiTestCase(MyApiTestCase):
    def test_01_auth_with_split(self):
        set_privacyidea_config("splitAtSign", "1")
        self.setUp_user_realms()
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            self.assertEqual('realm1', result['value']['realm'], result)

        # test failed auth
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "password": "false"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Wrong credentials',
                             result['error']['message'], result)

        # test with realm added to user
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius@realm1",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(200, res.status_code, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            self.assertEqual('realm1', result['value']['realm'], result)

        # test with realm added to user and unknown realm param
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius@realm1",
                                                 "realm": "unknown",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Unknown realm: unknown.',
                             result['error']['message'], result)

        # test with realm parameter
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "realm": "realm1",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(200, res.status_code, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            self.assertEqual('realm1', result['value']['realm'], result)

        # test with broken realm parameter
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "realm": "unknown",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Unknown realm: unknown.',
                             result['error']['message'], result)

        # test with empty realm parameter
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "realm": "",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(200, res.status_code, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            # realm1 should be the default realm
            self.assertEqual('realm1', result['value']['realm'], result)

        # test with realm parameter and wrong realm added to user
        with mock.patch("logging.Logger.error") as mock_log:
            with self.app.test_request_context('/auth',
                                               method='POST',
                                               data={"username": "cornelius@unknown",
                                                     "realm": "realm1",
                                                     "password": "test"}):
                res = self.app.full_dispatch_request()
                self.assertEqual(401, res.status_code, res)
                result = res.json.get("result")
                self.assertFalse(result.get("status"), result)
            mock_log.assert_called_once_with("The user User(login='cornelius@unknown',"
                                             " realm='realm1', resolver='') exists"
                                             " in NO resolver.")

        # test with wrong realm parameter and wrong realm added to user
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius@unknown",
                                                 "realm": "anotherunknown",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Unknown realm: anotherunknown.',
                             result['error']['message'], result)

        # Now we take it up one notch and add another resolver
        self.setUp_user_realm3()
        # The selfservice user does not exist in realm3
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "selfservice@realm3",
                                                 "realm": "realm1",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(200, res.status_code, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            self.assertEqual('realm1', result['value']['realm'], result)

        # and the other way round
        with mock.patch("logging.Logger.error") as mock_log:
            with self.app.test_request_context('/auth',
                                               method='POST',
                                               data={"username": "selfservice@realm1",
                                                     "realm": "realm3",
                                                     "password": "test"}):
                res = self.app.full_dispatch_request()
                self.assertEqual(401, res.status_code, res)
                result = res.json.get("result")
                self.assertFalse(result.get("status"), result)
                self.assertEqual(4031, result['error']['code'], result)
                self.assertEqual('Authentication failure. Wrong credentials',
                                 result['error']['message'], result)
            # the realm will be split from the login name
            mock_log.assert_called_once_with("The user User(login='selfservice',"
                                             " realm='realm3', resolver='') exists"
                                             " in NO resolver.")

    # And now we do all of the above without the splitAtSign setting
    def test_02_auth_without_split(self):
        set_privacyidea_config("splitAtSign", "0")
        self.setUp_user_realms()
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            self.assertEqual('realm1', result['value']['realm'], result)

        # test failed auth
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "password": "false"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Wrong credentials',
                             result['error']['message'], result)

        # test with realm added to user. This fails since we do not split
        with mock.patch("logging.Logger.error") as mock_log:
            with self.app.test_request_context('/auth',
                                               method='POST',
                                               data={"username": "cornelius@realm1",
                                                     "password": "test"}):
                res = self.app.full_dispatch_request()
                self.assertEqual(401, res.status_code, res)
                result = res.json.get("result")
                self.assertFalse(result.get("status"), result)
                self.assertEqual(4031, result['error']['code'], result)
                self.assertEqual('Authentication failure. Wrong credentials',
                                 result['error']['message'], result)
            mock_log.assert_called_once_with("The user User(login='cornelius@realm1',"
                                             " realm='realm1', resolver='') exists"
                                             " in NO resolver.")

        # test with realm added to user and unknown realm param
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius@realm1",
                                                 "realm": "unknown",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Unknown realm: unknown.',
                             result['error']['message'], result)

        # test with realm parameter
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "realm": "realm1",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(200, res.status_code, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            self.assertEqual('realm1', result['value']['realm'], result)

        # test with broken realm parameter
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "realm": "unknown",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Unknown realm: unknown.',
                             result['error']['message'], result)

        # test with empty realm parameter
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius",
                                                 "realm": "",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(200, res.status_code, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), result)
            self.assertIn('token', result.get("value"), result)
            # realm1 should be the default realm
            self.assertEqual('realm1', result['value']['realm'], result)

        # test with realm parameter and wrong realm added to user
        with mock.patch("logging.Logger.error") as mock_log:
            with self.app.test_request_context('/auth',
                                               method='POST',
                                               data={"username": "cornelius@unknown",
                                                     "realm": "realm1",
                                                     "password": "test"}):
                res = self.app.full_dispatch_request()
                self.assertEqual(401, res.status_code, res)
                result = res.json.get("result")
                self.assertFalse(result.get("status"), result)
            mock_log.assert_called_once_with("The user User(login='cornelius@unknown',"
                                             " realm='realm1', resolver='') exists"
                                             " in NO resolver.")

        # test with wrong realm parameter and wrong realm added to user
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "cornelius@unknown",
                                                 "realm": "anotherunknown",
                                                 "password": "test"}):
            res = self.app.full_dispatch_request()
            self.assertEqual(401, res.status_code, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), result)
            self.assertEqual(4031, result['error']['code'], result)
            self.assertEqual('Authentication failure. Unknown realm: anotherunknown.',
                             result['error']['message'], result)

        # Now we take it up one notch and add another resolver
        self.setUp_user_realm3()
        # The selfservice user does not exist in realm3
        with mock.patch("logging.Logger.error") as mock_log:
            with self.app.test_request_context('/auth',
                                               method='POST',
                                               data={"username": "selfservice@realm3",
                                                     "realm": "realm1",
                                                     "password": "test"}):
                res = self.app.full_dispatch_request()
                self.assertEqual(401, res.status_code, res)
                result = res.json.get("result")
                self.assertFalse(result.get("status"), result)
                self.assertEqual(4031, result['error']['code'], result)
            mock_log.assert_called_once_with("The user User(login='selfservice@realm3',"
                                             " realm='realm1', resolver='') exists"
                                             " in NO resolver.")

        # and the other way round
        with mock.patch("logging.Logger.error") as mock_log:
            with self.app.test_request_context('/auth',
                                               method='POST',
                                               data={"username": "selfservice@realm1",
                                                     "realm": "realm3",
                                                     "password": "test"}):
                res = self.app.full_dispatch_request()
                self.assertEqual(401, res.status_code, res)
                result = res.json.get("result")
                self.assertFalse(result.get("status"), result)
                self.assertEqual(4031, result['error']['code'], result)
                self.assertEqual('Authentication failure. Wrong credentials',
                                 result['error']['message'], result)
            # the realm will be split from the login name
            mock_log.assert_called_once_with("The user User(login='selfservice@realm1',"
                                             " realm='realm3', resolver='') exists"
                                             " in NO resolver.")
