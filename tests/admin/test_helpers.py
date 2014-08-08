import unittest
from admin import app
from admin.helpers import requires_authentication
from hamcrest import assert_that, equal_to
from mock import patch


class HelpersTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    @patch('admin.helpers.get_context')
    def test_requires_login_redirects_when_no_user(self, get_context_mock):
        get_context_mock.return_value = {}
        func = lambda x: x
        wrapped_app_method = requires_authentication(func)
        with app.test_request_context('/protected-resource', method='GET'):
            response = wrapped_app_method()

        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], equal_to('/'))
