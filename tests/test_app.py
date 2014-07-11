import json
import unittest
from admin import app
from hamcrest import assert_that, equal_to


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.app.test_client()

    def test_status_endpoint_returns_ok(self):
        response = self.app.get("/_status")
        assert_that(response.status_code, equal_to(200))
        assert_that(json.loads(response.data), equal_to({"admin": "ok"}))
