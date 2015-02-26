from mock import patch, Mock
from nose.tools import assert_equal
from hamcrest import assert_that, equal_to, ends_with, contains_string

from tests.admin.support.flask_app_test_case import(
    FlaskAppTestCase,
    signed_in)

from admin import app
from admin.authentication import get_authorization_url
from admin.redis_session import RedisSession
from requests import ConnectionError, Timeout


@patch('requests_oauthlib.OAuth2Session.fetch_token')
@patch('requests_oauthlib.OAuth2Session.get')
@patch('requests_oauthlib.OAuth2Session.authorization_url')
class AuthenticationTestCase(FlaskAppTestCase):

    @signed_in()
    def test_signout_redirects_properly_and_clears_session(
            self,
            oauth_authorization_url_patch,
            oauth_get_patch,
            oauth_fetch_token_patch,
            client):
        response = client.get("/sign-out")
        assert_that(response.status_code, equal_to(302))
        assert_that(
            response.headers['Location'], ends_with('/users/sign_out'))
        with client.session_transaction() as session:
            assert_that(
                session,
                equal_to({}))

    def test_signin_development_route(
            self,
            oauth_authorization_url_patch,
            oauth_get_patch,
            oauth_fetch_token_patch):
        response = self.client.get("/sign-in")
        assert_that(response.status_code, equal_to(302))
        assert_that(
            response.headers['Location'], ends_with('/'))
        with self.client.session_transaction() as session:
            assert_that(
                session['oauth_token']['access_token'],
                equal_to(app.config['FAKE_OAUTH_TOKEN']))
            assert_that(
                session['oauth_user'],
                equal_to(app.config['FAKE_OAUTH_USER']))

    def test_authorize_sets_correct_session_if_user_can_sign_in(
            self,
            oauth_authorization_url_patch,
            oauth_get_patch,
            oauth_fetch_token_patch):
        token = "token_token"
        user = {
            'permissions': ['signin'],
            'uid': "bleep_bloop_blarp"
        }
        oauth_get_response = Mock()
        oauth_get_response.json = Mock(return_value={
            'user': user
        })
        oauth_get_patch.return_value = oauth_get_response
        oauth_fetch_token_patch.return_value = token
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = "foo"
        response = self.client.get(
            '/auth/gds/callback')
        self.assert_session_contains('oauth_user', user)
        self.assert_session_contains('oauth_token', token)
        self.assert_flashes('You have been successfully signed in')
        assert_equal(response.headers['Location'], 'http://localhost/')
        assert_equal(response.status_code, 302)

    def test_authorize_sends_client_id_with_user_json(
            self,
            oauth_authorization_url_patch,
            oauth_get_patch,
            oauth_fetch_token_patch):
        token = "token_token"
        user = {
            'permissions': ['signin'],
            'uid': "bleep_bloop_blarp"
        }
        oauth_get_response = Mock()
        oauth_get_response.json = Mock(return_value={
            'user': user
        })
        oauth_get_patch.return_value = oauth_get_response
        oauth_fetch_token_patch.return_value = token
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = "foo"
        response = self.client.get(
            '/auth/gds/callback')

        oauth_get_patch.assert_called_with(
            'http://signon.dev.gov.uk/user.json?client_id=oauth_id')

    def test_authorize_does_not_sign_in_if_user_cannot_sign_in(
            self,
            oauth_authorization_url_patch,
            oauth_get_patch,
            oauth_fetch_token_patch):
        token = "token_token"
        user = {
            'permissions': [],
            'uid': "bleep_bloop_blarp"
        }
        oauth_get_response = Mock()
        oauth_get_response.json = Mock(return_value={
            'user': user
        })
        oauth_get_patch.return_value = oauth_get_response
        oauth_fetch_token_patch.return_value = token
        with self.client.session_transaction() as sess:
            sess['oauth_state'] = "foo"
        response = self.client.get(
            '/auth/gds/callback')
        self.assert_session_contains('oauth_user', user)
        self.assert_session_contains('oauth_token', token)
        assert_equal(len(self.get_flashes()), 0)
        assert_equal(response.headers['Location'], 'http://localhost/')
        assert_equal(response.status_code, 302)

    def test_get_authorization_url_sets_oauth_state_returns_url(
            self,
            oauth_authorization_url_patch,
            oauth_get_patch,
            oauth_fetch_token_patch):
        oauth_authorization_url_patch.return_value = ('some url', 'state')
        session = {}
        assert_equal(get_authorization_url(session), 'some url')
        assert_equal(session, {'oauth_state': 'state'})


@patch('requests_oauthlib.OAuth2Session.get')
@patch('admin.redis_session.RedisSession.delete_sessions_for_user')
class SignonCallbacksTestCase(FlaskAppTestCase):

    def setUp(self):
        super(SignonCallbacksTestCase, self).setUp()
        self.headers = [('Authorization', 'Bearer foobar')]

    def test_reauth_with_invalid_user(
            self,
            session_delete_sessions_for_user_patch,
            oauth_get_patch):
        # Set up the Mock for calling Signon
        self.mock_signon_json(
            oauth_get_patch).return_value = self.not_allowed_user_update_json()
        self.expect_session_unchanged(session_delete_sessions_for_user_patch)

        response = self.do_reauth_post()
        self.assertEqual(403, response.status_code, response.data)

    def test_reauth_when_invalid_json(
            self,
            session_delete_sessions_for_user_patch,
            oauth_get_patch):
        # Set up the Mock for calling Signon
        self.mock_signon_json(oauth_get_patch).side_effect = ValueError()
        self.expect_session_unchanged(session_delete_sessions_for_user_patch)

        response = self.do_reauth_post()
        self.assertEqual(500, response.status_code, response.data)

    def test_reauth_with_valid_user(
            self,
            session_delete_sessions_for_user_patch,
            oauth_get_patch):
        # Set up the Mock for calling Signon
        self.mock_signon_json(
            oauth_get_patch).return_value = self.allowed_user_update_json()

        response = self.do_reauth_post()

        self.assertEqual(200, response.status_code, response.data)

        session_delete_sessions_for_user_patch.assert_called_with('user-uid')

    def test_reauth_when_signon_down(
            self,
            session_delete_sessions_for_user_patch,
            oauth_get_patch):
        # Set up the Mock for calling Signon
        oauth_get_patch.side_effect = ConnectionError()
        self.expect_session_unchanged(session_delete_sessions_for_user_patch)

        response = self.do_reauth_post()
        # assert no session was cleared
        self.assertEqual(500, response.status_code, response.data)

    def test_reauth_when_signon_really_slow(
            self,
            session_delete_sessions_for_user_patch,
            oauth_get_patch):
        # Set up the Mock for calling Signon
        oauth_get_patch.side_effect = Timeout()
        self.expect_session_unchanged(session_delete_sessions_for_user_patch)

        response = self.do_reauth_post()
        # assert no session was cleared
        self.assertEqual(500, response.status_code, response.data)

    def test_reauth_when_signon_unauthenticated(
            self,
            session_delete_sessions_for_user_patch,
            oauth_get_patch):
        # Set up the Mock for calling Signon
        oauth_get_patch.return_value.status_code = 401
        self.expect_session_unchanged(session_delete_sessions_for_user_patch)

        response = self.do_reauth_post()
        self.assertEqual(401, response.status_code, response.data)

    def mock_signon_json(self, mock_signon):
        return mock_signon.return_value.json

    def expect_session_unchanged(self, session_delete_sessions_for_user_patch):
        # assert that the sessions weren't updated. If this is caused, then
        # things should fail in tests.
        session_delete_sessions_for_user_patch.side_effect = Exception(
            "Unexpected session alteration")

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
        return self.client.post(
            '/auth/gds/api/users/user-uid/reauth', headers=self.headers)
