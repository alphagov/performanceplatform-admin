import json
import unittest
from admin import app
from hamcrest import assert_that, equal_to
from httmock import urlmatch, HTTMock


@urlmatch(netloc=r'[a-z]+\.development\.performance\.service\.gov\.uk$')
def performance_platform_status_mock(url, request):
    return json.dumps({'status': 'ok'})


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

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
