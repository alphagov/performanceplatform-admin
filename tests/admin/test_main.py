import json
import unittest
from admin import app
from hamcrest import assert_that, equal_to, ends_with
from httmock import urlmatch, HTTMock
from mock import patch


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
