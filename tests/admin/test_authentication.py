import unittest
from mock import patch
from admin.authentication import validate_bearer_token
from admin import app
from nose.tools import raises, assert_equal, nottest
from werkzeug.exceptions import Forbidden
from requests import ConnectionError


class BearerTokenTestCase(unittest.TestCase):
    @raises(Forbidden)
    def test_single_word_bearer_token_invalid(self):
        validate_bearer_token({'Authorization': 'bob'})

    @raises(Forbidden)
    def test_malformed_or_missing_auth_header_invalid(self):
        validate_bearer_token({'Authorizaation': 'bob'})

    @raises(Forbidden)
    def test_missing_bearer_with_more_than_one_space_invalid(self):
        validate_bearer_token({'Authorizaation': 'bob bob bob'})

    @raises(Forbidden)
    def test_header_without_bearer_invalid(self):
        validate_bearer_token({'Authorization': 'bob bob'})

    def test_valid_bearer_token(self):
        assert_equal('bob', validate_bearer_token(
            {'Authorization': 'Bearer bob'}))


@patch('admin.authentication.session')
@patch('admin.authentication.OAuth2Session')
class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SIGNON_OAUTH_ID'] = 'test-oauth-id'
        self.app = app.test_client()
        self.headers = [('Authorization', 'Bearer foobar')]

    def test_reauth_with_valid_user(
            self, mock_sso_session_constructor, mock_session):
        self.sso_session_json_mock(
            mock_sso_session_constructor
        ).return_value = self.allowed_user_update_json()
        response = self.do_reauth_post()
        mock_sso_session_constructor.assert_called_with(
            'test-oauth-id',
            token={'access_token': u'foobar', 'type': 'Bearer'})
        mock_session.delete_sessions_for_user.assert_called_with('user')
        self.assertEqual(200, response.status_code)

    def test_reauth_with_invalid_user(
            self, mock_sso_session_constructor, mock_session):
        self.sso_session_json_mock(
            mock_sso_session_constructor
        ).return_value = self.not_allowed_user_update_json()
        response = self.do_reauth_post()
        # assert no session was cleared
        self.assertItemsEqual([], mock_session.call_args_list)
        self.assertEqual(403, response.status_code)

    def test_reauth_when_invalid_json(
            self, mock_sso_session_constructor, mock_session):
        self.sso_session_json_mock(
            mock_sso_session_constructor).side_effect = ValueError()
        response = self.do_reauth_post()
        # assert no session was cleared
        self.assertEqual(500, response.status_code)

    def test_reauth_when_signon_down(
            self, mock_sso_session_constructor, mock_session):
        self.sso_session_get_mock(
            mock_sso_session_constructor).side_effect = ConnectionError()
        response = self.do_reauth_post()
        # assert no session was cleared
        self.assertEqual(500, response.status_code)

    def test_reauth_when_signon_unauthenticated(
            self, mock_sso_session_constructor, mock_session):
        self.sso_session_get_mock(
            mock_sso_session_constructor).return_value.status_code = 401
        response = self.do_reauth_post()
        # assert no session was cleared
        self.assertEqual(401, response.status_code)

    def sso_session_json_mock(self, session_mock):
        return self.sso_session_get_mock(session_mock).return_value.json

    def sso_session_get_mock(self, session_mock):
        return session_mock.return_value.get

    def allowed_user_update_json(self):
        return self.create_user_json(['user_update_permission'])

    def not_allowed_user_update_json(self):
        return self.create_user_json([])

    def create_user_json(self, permissions):
        user = {}
        user['user'] = {}
        user['user']['permissions'] = permissions
        return user

    def do_reauth_post(self):
        return self.app.post(
            '/auth/gds/api/users/user/reauth', headers=self.headers)


class RealAuthenticationTestCase(unittest.TestCase):

    """ Make a real request to signon

    Can be useful for testing real signon requests
    """

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SIGNON_OAUTH_ID'] = 'test-oauth-id'
        self.app = app.test_client()
        self.headers = [('Authorization', 'Bearer foobar')]

    # isn't this kind of a test?
    @nottest
    def test_reauth_with_valid_user(self):
        response = self.do_reauth_post()
        self.assertEqual(200, response.status_code)

    def do_reauth_post(self):
        return self.app.post(
            '/auth/gds/api/users/user/reauth', headers=self.headers)
