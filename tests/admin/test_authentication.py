from mock import patch, Mock
from nose.tools import assert_equal
from hamcrest import assert_that, equal_to, ends_with, contains_string

from tests.admin.support.flask_app_test_case import(
    FlaskAppTestCase,
    signed_in)

from admin.authentication import get_authorization_url


@patch('requests_oauthlib.OAuth2Session.fetch_token')
@patch('requests_oauthlib.OAuth2Session.get')
@patch('requests_oauthlib.OAuth2Session.authorization_url')
class AuthenticationTestCase(FlaskAppTestCase):
    @signed_in
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
