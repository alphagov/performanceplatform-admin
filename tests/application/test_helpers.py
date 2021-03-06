import unittest
from application import app
from application.helpers import(
    requires_authentication,
    requires_feature,
    signed_in,
    group_by_group,
    signed_in_no_access,
    no_access,
    has_user_with_token,
    view_helpers,
    user_has_feature,
)
from hamcrest import assert_that, equal_to, is_
from mock import patch


class HelpersTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_view_helper_user_has_feature(self):
        user_has_feature = view_helpers()['user_has_feature']
        assert_that(user_has_feature('edit-dashboards', {}), is_(False))
        assert_that(user_has_feature('edit-dashboards',
                                     {'permissions': ['signin']}),
                    is_(False))
        assert_that(user_has_feature('edit-dashboards',
                                     {'permissions': ['dashboard-editor']}),
                    is_(True))

    @patch('application.helpers.signed_in')
    def test_requires_login_redirects_when_no_user(self, signed_in_mock):
        signed_in_mock.return_value = False
        func = lambda x: x
        wrapped_app_method = requires_authentication(func)
        with app.test_request_context('/protected-resource', method='GET'):
            response = wrapped_app_method()

        assert_that(response.status_code, equal_to(302))
        assert_that(response.headers['Location'], equal_to('/'))

    @patch('application.helpers.signed_in')
    def test_requires_feature_allows_access(self, signed_in_mock):
        signed_in_mock.return_value = True
        func = lambda: 'Decorator exited successfully'
        wrapped_app_method = requires_feature('big-edit')

        with app.test_request_context('/protected', method='GET') as context:
            context.session.update({
                'oauth_user': {'permissions': ['admin']},
            })
            response = wrapped_app_method(func)()

        assert_that(response, is_('Decorator exited successfully'))

    @patch('application.helpers.signed_in')
    def test_requires_feature_redirects_when_not_signed_in(
            self, signed_in_mock):
        signed_in_mock.return_value = False
        func = lambda: 'Decorator exited successfully'
        wrapped_app_method = requires_feature('some-feature')

        with app.test_request_context('/protected', method='GET') as context:
            response = wrapped_app_method(func)()

        assert_that(response.status_code, is_(302))
        assert_that(response.headers['Location'], is_('/'))

    @patch('application.helpers.signed_in')
    def test_requires_feature_redirects_for_bad_permissions(
            self, signed_in_mock):
        signed_in_mock.return_value = True
        func = lambda: 'Decorator exited successfully'
        wrapped_app_method = requires_feature('some-feature')

        with app.test_request_context('/protected', method='GET') as context:
            context.session.update({
                'oauth_user': {'permissions': ['normal-permission']},
            })
            response = wrapped_app_method(func)()

        assert_that(response.status_code, is_(302))
        assert_that(response.headers['Location'], is_('/'))

    def test_has_user_with_token_returns_true_when_session_has_token_and_user(
            self):
        assert_that(has_user_with_token({
            'oauth_token': {
                'access_token': 'token'
            },
            'oauth_user': "bleep_bloop_blarp"
        }), equal_to(True))

    def test_has_user_with_token_false_when_session_has_no_token(self):
        assert_that(has_user_with_token({
            'oauth_user': "bleep_bloop_blarp"
        }), equal_to(False))

    def test_has_user_with_token_false_when_session_token_has_no_access_token(
            self):
        assert_that(has_user_with_token({
            'oauth_token': {
            },
            'oauth_user': "bleep_bloop_blarp"
        }), equal_to(False))

    def test_has_user_with_token_is_false_when_session_has_no_user(self):
        assert_that(has_user_with_token({
            'oauth_token': {
                'access_token': 'token'
            }
        }), equal_to(False))

    def test_has_user_with_token_is_false_when_empty_session(self):
        assert_that(has_user_with_token({}), equal_to(False))

    def test_no_access_true_if_session_user_has_no_permissions(self):
        assert_that(no_access({}), equal_to(True))

    def test_no_access_true_if_session_user_hasnt_signin_permission(self):
        assert_that(no_access({
            'permissions': []
        }), equal_to(True))

    def test_no_access_false_if_session_user_has_signin_permission(
            self):
        assert_that(no_access({
            'permissions': ['signin']
        }), equal_to(False))

    @patch('application.helpers.has_user_with_token')
    @patch('application.helpers.no_access')
    def test_signed_in_true_when_has_user_with_token_and_not_no_access(
            self,
            no_access_patch,
            has_user_with_token_patch):
        has_user_with_token_patch.return_value = True
        no_access_patch.return_value = False
        assert_that(signed_in({'oauth_user': 'user'}), equal_to(True))

    @patch('application.helpers.has_user_with_token')
    def test_signed_in_false_when_hasnt_user_with_token(
            self,
            has_user_with_token_patch):
        has_user_with_token_patch.return_value = False
        assert_that(signed_in({'oauth_user': 'user'}), equal_to(False))

    @patch('application.helpers.has_user_with_token')
    @patch('application.helpers.no_access')
    def test_signed_in_false_when_has_user_with_token_and_no_access(
            self,
            no_access_patch,
            has_user_with_token_patch):
        has_user_with_token_patch.return_value = True
        no_access_patch.return_value = True
        assert_that(signed_in({'oauth_user': 'user'}), equal_to(False))

    @patch('application.helpers.has_user_with_token')
    @patch('application.helpers.no_access')
    def test_signed_in_no_access_false_if_signed_in_and_not_no_access(
            self,
            no_access_patch,
            has_user_with_token_patch):
        has_user_with_token_patch.return_value = True
        no_access_patch.return_value = False
        assert_that(signed_in_no_access(
            {'oauth_user': 'user'}), equal_to(False))

    @patch('application.helpers.has_user_with_token')
    def test_signed_in_no_access_false_when_hasnt_user_with_token(
            self,
            has_user_with_token_patch):
        has_user_with_token_patch.return_value = False
        assert_that(signed_in_no_access(
            {'oauth_user': 'user'}), equal_to(False))

    @patch('application.helpers.has_user_with_token')
    @patch('application.helpers.no_access')
    def test_signed_in_no_access_true_when_has_user_with_token_and_no_access(
            self,
            no_access_patch,
            has_user_with_token_patch):
        has_user_with_token_patch.return_value = True
        no_access_patch.return_value = True
        assert_that(signed_in_no_access(
            {'oauth_user': 'user'}), equal_to(True))

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

    def test_admin_user_has_bigedit_feature(self):
        user = {'permissions': ['admin']}
        assert_that(user_has_feature('big-edit', user), equal_to(True))

    def test_dashboard_editor_user_does_not_have_bigedit_feature(self):
        user = {'permissions': ['dashboard-editor']}
        assert_that(user_has_feature('big-edit', user), equal_to(False))

    def test_dashboard_editor_and_admin_user_does_have_bigedit_feature(self):
        user = {'permissions': ['dashboard-editor', 'admin']}
        assert_that(user_has_feature('big-edit', user), equal_to(True))

    def test_user_with_permissions_not_in_list_features(self):
        user = {'permissions': ['signin']}
        assert_that(user_has_feature('big-edit', user), equal_to(False))
