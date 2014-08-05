import json
import unittest
from admin import app
from hamcrest import assert_that, equal_to, ends_with
from httmock import urlmatch, HTTMock
from mock import patch, Mock
import requests
from admin.main import get_context


@urlmatch(netloc=r'[a-z]+\.development\.performance\.service\.gov\.uk$')
def performance_platform_status_mock(url, request):
    return json.dumps({'status': 'ok'})


class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    @patch('admin.main.get_context')
    def test_homepage_redirects_when_signed_in(self, get_context_mock):
        get_context_mock.return_value = {'user': {'email': 'test@example.com'}}
        response = self.app.get('/')
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], ends_with('/data-sets'))

    def test_status_endpoint_returns_ok(self):
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

    def test_requires_authentication_redirects_when_no_auth_on_data_sets(
            self):
        with HTTMock(performance_platform_status_mock):
            response = self.app.get("/data-sets")
        assert_that(response.status_code, equal_to(302))
        assert_that(
            response.headers['Location'],
            equal_to('http://localhost/'))

    @patch('admin.main.get_context')
    def test_requires_authentication_continues_when_auth_on_data_sets(
            self,
            get_context_mock):
        get_context_mock.return_value = {
            'user': {
                'email': 'test@example.com'
            },
            'environment': {}
        }
        with HTTMock(performance_platform_status_mock):
            response = self.app.get("/data-sets")
        assert_that(response.status_code, equal_to(200))

    def test_requires_authentication_redirects_when_no_auth_on_upload_error(
            self):
        with HTTMock(performance_platform_status_mock):
            response = self.app.get("/upload-error")
        assert_that(response.status_code, equal_to(302))
        assert_that(
            response.headers['Location'],
            equal_to('http://localhost/'))

    @patch('admin.main.get_context')
    def test_requires_authentication_continues_when_auth_on_upload_error(
            self,
            get_context_mock):
        get_context_mock.return_value = {
            'user': {
                'email': 'test@example.com'
            },
            'environment': {}
        }
        with HTTMock(performance_platform_status_mock):
            response = self.app.get("/upload-error")
        assert_that(response.status_code, equal_to(200))

    def test_signout_redirects_properly(self):
        response = self.app.get("/sign-out")
        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], ends_with('/users/sign_out'))

    @patch('requests.get')
    def test_get_context_returns_no_user_or_datasets_on_403(
            self,
            mock_get_request):
        bad_response = requests.Response()
        bad_response.status_code = 403
        mock_get_request.return_value = bad_response
        session_context = get_context({
            'oauth_token': {
                'access_token': 'token'},
            'oauth_user': 'a user'})
        assert_that(session_context, equal_to({
            'environment': {
                'human_name': 'Development',
                'name': 'development'}}))

    @patch('requests.get')
    def test_get_context_returns_user_and_datasets_on_200(
            self,
            mock_get_request):
        good_response = requests.Response()
        good_response.status_code = 200
        mock_json = Mock()
        mock_json.return_value = json.dumps({})
        good_response.json = mock_json
        mock_get_request.return_value = good_response
        session_context = get_context({
            'oauth_token': {
                'access_token': 'token'},
            'oauth_user': 'a user'})
        assert_that(session_context, equal_to({
            'environment': {
                'human_name': 'Development',
                'name': 'development'},
            'data_sets': '{}',
            'user': 'a user'}))
