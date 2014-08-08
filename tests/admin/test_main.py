import json
from tests.admin.support.flask_app_test_case import FlaskAppTestCase
from admin import app
from hamcrest import assert_that, equal_to, ends_with
from httmock import urlmatch, HTTMock
from mock import patch


@urlmatch(netloc=r'[a-z]+\.development\.performance\.service\.gov\.uk$')
def performance_platform_status_mock(url, request):
    return json.dumps({'status': 'ok'})


class AppTestCase(FlaskAppTestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    @patch('admin.main.signed_in')
    def test_homepage_redirects_when_signed_in(self, signed_in):
        signed_in.return_value = True
        response = self.app.get('/')
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], ends_with('/upload-data'))

    def test_status_endpoint_returns_ok(self):
        with HTTMock(performance_platform_status_mock):
            response = self.app.get("/_status")
        assert_that(response.status_code, equal_to(200))
        assert_that(json.loads(response.data)['admin'],
                    equal_to({"status": "ok"}))

    def test_status_endpoint_returns_dependent_app_status(self):
        with HTTMock(performance_platform_status_mock):
            response = self.app.get("/_status")
        assert_that(response.status_code, equal_to(200))
        assert_that(json.loads(response.data)['stagecraft'],
                    equal_to({"status": "ok"}))
        assert_that(json.loads(response.data)['backdrop'],
                    equal_to({"status": "ok"}))

    def test_signout_redirects_properly_and_clears_session(self):
        with self.client as client:
            with client.session_transaction() as sess:
                sess.update({
                    'oauth_token': {
                        'access_token': 'token'},
                    'oauth_user': 'a user'})
            response = client.get("/sign-out")
            assert_that(response.status_code, equal_to(302))
            assert_that(
                response.headers['Location'], ends_with('/users/sign_out'))
            with client.session_transaction() as sess:
                assert_that(
                    sess,
                    equal_to({}))
