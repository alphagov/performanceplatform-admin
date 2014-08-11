import unittest
from admin import app
from admin.helpers import requires_authentication, signed_in, group_by_group
from hamcrest import assert_that, equal_to
from mock import patch


class HelpersTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    @patch('admin.helpers.signed_in')
    def test_requires_login_redirects_when_no_user(self, signed_in_mock):
        signed_in_mock.return_value = False
        func = lambda x: x
        wrapped_app_method = requires_authentication(func)
        with app.test_request_context('/protected-resource', method='GET'):
            response = wrapped_app_method()

        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], equal_to('/'))

    def test_signed_in_is_true_when_user_has_partial_session(self):
        assert_that(signed_in({
            'oauth_token': {
                'access_token': 'token'},
            'oauth_user': 'a user'}), equal_to(True))

    def test_signed_in_is_false_when_users_signed_in(self):
        assert_that(signed_in({
            'oauth_user': 'a user'}), equal_to(False))

    def test_signed_in_is_false_when_user_not_signed_in(self):
        assert_that(signed_in({}), equal_to(False))

    def test_group_by_group_groups_datasets_by_group(self):
        data_sets = [
            {
                'data_group': "group_1",
                'data_type': "type1"
            },
            {
                'data_group': "group_1",
                'data_type': "type2"
            },
            {
                'data_group': "group_2",
                'data_type': "type3"
            }
        ]
        grouped_data_sets = {
            "group_1": [
                {
                    'data_group': "group_1",
                    'data_type': "type1"
                },
                {
                    'data_group': "group_1",
                    'data_type': "type2"
                }
            ],
            "group_2": [
                {
                    'data_group': "group_2",
                    'data_type': "type3"
                }
            ]
        }
        assert_that(group_by_group(data_sets), equal_to(grouped_data_sets))
