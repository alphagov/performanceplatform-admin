from tests.application.support.flask_app_test_case import FlaskAppTestCase
from application import app
from hamcrest import (
    assert_that,
    equal_to,
    contains_string,
    ends_with,
    has_entries,
    match_equality
)
from mock import patch


class AddUserSatisfactionTestCase(FlaskAppTestCase):

    @staticmethod
    def params(options={}):
        params = {
            'done_page_url': 'http://www.gov.uk/done/apply-some-transaction'}
        params.update(options)
        return params

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard']
            }

    def test_authenticated_user_is_required(self):
        with self.client.session_transaction() as session:
            del session['oauth_token']
        response = self.client.get(
            '/dashboard/dashboard-uuid/user-satisfaction/add')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get(
            '/dashboard/dashboard-uuid/user-satisfaction/add')
        assert_that(response.status, equal_to('302 FOUND'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    def test_add_user_satisfaction_slug_renders_done_page_URL_form(
            self, mock_get_dashboard):
        response = self.client.get(
            '/dashboard/dashboard-uuid/user-satisfaction/add')
        assert_that(response.status, equal_to('200 OK'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    def test_done_page_URL_field_is_required(self, mock_get_dashboard):
        data = self.params({'done_page_url': ''})
        response = self.client.post(
            '/dashboard/dashboard-uuid/user-satisfaction/add', data=data)
        assert_that(response.data, contains_string(
            'cannot be blank'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    def test_done_page_url_is_like_a_url(self, mock_get_dashboard):
        data = self.params({'done_page_url': 'www.foo..com'})
        response = self.client.post(
            'dashboard/dashboard-uuid/user-satisfaction/add', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data,
                    contains_string('Done page URL format is invalid'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    @patch("performanceplatform.client.admin.AdminAPI.get_data_set")
    @patch("performanceplatform.client.admin.AdminAPI.add_module_to_dashboard")
    @patch("performanceplatform.client.admin.AdminAPI.list_module_types")
    def test_creates_a_module_if_a_user_satisfaction_data_set_exists(
            self,
            mock_list_module_types,
            mock_add_module_to_dashboard,
            mock_get_data_set,
            mock_get_dashboard):
        mock_get_data_set.return_value = {
            'name': 'apply_some_transaction_user_satisfaction_score'}
        mock_list_module_types.return_value = [{
            'id': 'module-type-uuid',
            'name': 'user_satisfaction_graph'}]
        self.client.post(
            '/dashboard/dashboard-uuid/user-satisfaction/add',
            data=self.params())
        mock_add_module_to_dashboard.assert_called_once_with(
            'dashboard-uuid',
            match_equality(has_entries({
                'slug': 'user-satisfaction',
                'data_group': 'apply-some-transaction',
                'data_type': 'user-satisfaction-score',
                'type_id': 'module-type-uuid'}))
        )

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    @patch("performanceplatform.client.admin.AdminAPI.get_data_set")
    @patch("performanceplatform.client.admin.AdminAPI.list_module_types")
    @patch("performanceplatform.client.admin.AdminAPI.add_module_to_dashboard")
    def test_redirects_to_dashboard_hub_page(
            self,
            mock_add_module_to_dashboard,
            mock_list_module_types,
            mock_get_data_set,
            mock_get_dashboard):
        mock_list_module_types.return_value = [{
            'id': 'module-type-uuid',
            'name': 'user_satisfaction_graph'}]
        response = self.client.post(
            '/dashboard/dashboard-uuid/user-satisfaction/add',
            data=self.params())
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('dashboards/dashboard-uuid'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    def test_renders_a_contact_us_page_if_unable_to_extract_done_page(
            self, mock_get_dashboard):
        params = self.params({
            'done_page_url': 'http://www.gov.uk/some-transaction'})
        response = self.client.post(
            '/dashboard/dashboard-uuid/user-satisfaction/add',
            data=params)
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/get-in-touch'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value={})
    @patch("performanceplatform.client.admin.AdminAPI.get_data_set")
    @patch("performanceplatform.client.admin.AdminAPI.list_module_types")
    def test_renders_a_contact_us_page_if_no_user_satisfaction_data_set(
            self,
            mock_list_module_types,
            mock_get_data_set,
            mock_get_dashboard):
        mock_get_data_set.return_value = None
        response = self.client.post(
            '/dashboard/dashboard-uuid/user-satisfaction/add',
            data=self.params())
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/get-in-touch'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    def test_redirects_if_module_exists(self, mock_get_dashboard):

        mock_get_dashboard.return_value = {
            'id': 'dashboard-uuid',
            'title': 'A dashboard',
            'description': 'All about this dashboard',
            'slug': 'valid-slug',
            'owning_organisation': 'organisation-uuid',
            'dashboard_type': 'transaction',
            'customer_type': 'Business',
            'strapline': 'Dashboard',
            'business_model': 'Department budget',
            'published': False,
            'status': 'unpublished',
            'modules': [
                {'data_type': 'user-satisfaction-score'},
                {'slug': 'slug'}
            ]
        }

        response = self.client.get(
            '/dashboard/dashboard-uuid/user-satisfaction/add',
            data=self.params())

        assert_that(response.headers['Location'],
                    ends_with('/dashboards/dashboard-uuid'))
