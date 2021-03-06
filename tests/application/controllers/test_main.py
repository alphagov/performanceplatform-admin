import json
from tests.application.support.flask_app_test_case import(
    FlaskAppTestCase,
    signed_in)
from application import app
from hamcrest import assert_that, equal_to, ends_with, contains_string
from mock import patch, Mock
import requests


def okay_response():
    response = requests.Response()
    response.status_code = 200
    response.json = Mock(return_value={'status': 'ok'})
    return response


class AppTestCase(FlaskAppTestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    @patch('application.controllers.main.signed_in')
    def test_homepage_redirects_to_upload_when_signed_in(self, signed_in):
        signed_in.return_value = True
        response = self.app.get('/')
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], ends_with('/upload-data'))

    def test_homepage_renders_index_when_no_access(self):
        with self.app.session_transaction() as sess:
            sess.update({
                'oauth_token': {
                    'access_token': 'token'
                },
                'oauth_user': {
                    'name': 'Dave',
                    'permissions': []
                }
            })
        response = self.app.get('/')
        assert_that(response.status_code, equal_to(200))
        assert_that(response.data, contains_string(
            'You don\'t have access to this application.'))
        assert_that(response.data, contains_string(
            'Hello, Dave'))

    @patch('application.controllers.main.signed_in_no_access')
    @patch('application.controllers.main.get_authorization_url')
    def test_homepage_redirects_to_auth_url_when_possible_access(
            self,
            get_authorization_url_patch,
            signed_in_no_access):
        get_authorization_url_patch.return_value = "http://someurl.com"
        signed_in_no_access.return_value = False
        response = self.app.get('/')
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], equal_to(
            'http://someurl.com'))

    @patch("requests.get")
    def test_status_endpoint_returns_ok(self, get_patch):
        get_patch.return_value = okay_response()

        response = self.app.get("/_status")
        assert_that(response.status_code, equal_to(200))
        assert_that(json.loads(response.data)['status'],
                    equal_to('ok'))

    @patch("requests.get")
    def test_status_endpoint_returns_dependent_app_status(self, get_patch):
        get_patch.return_value = okay_response()

        response = self.app.get("/_status")
        assert_that(response.status_code, equal_to(200))
        assert_that(json.loads(response.data)['stagecraft'],
                    equal_to({"status": "ok"}))
        assert_that(json.loads(response.data)['backdrop'],
                    equal_to({"status": "ok"}))
