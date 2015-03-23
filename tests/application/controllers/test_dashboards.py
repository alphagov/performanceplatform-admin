from tests.application.support.flask_app_test_case import (
    FlaskAppTestCase,
    signed_in
)
from mock import patch, Mock
from application import app
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    has_entries
)
import os
import json
import requests


def dashboard_data(options={}):
    params = {
        'id': 'uuid',
        'title': 'A dashboard',
        'description': 'All about this dashboard',
        'slug': 'valid-slug',
        'owning_organisation': 'organisation-uuid',
        'dashboard_type': 'transaction',
        'customer_type': 'Business',
        'strapline': 'Dashboard',
        'business_model': 'Department budget'
    }
    params.update(options)
    return params


class DashboardHubPageTestCase(FlaskAppTestCase):

    @staticmethod
    def params(options={}):
        params = {
            'title': 'Foo Bar',
            'description': 'All about Foo Bar'
        }
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
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.status, equal_to('302 FOUND'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_dashboard_edit_slug_renders_dashboard_hub_page(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.status, equal_to('200 OK'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_dashboard_is_fetched(self, mock_get_dashboard):
        self.client.get('/dashboards/dashboard-uuid')
        mock_get_dashboard.assert_called_once_with('dashboard-uuid')

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    def test_dashboard_is_rendered(self, mock_get_dashboard):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../../fixtures/example-self-serve-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        mock_get_dashboard.return_value = dashboard_dict
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.data, contains_string('Patent renewals'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_dashboard_title_field_is_required(self, mock_get_dashboard):
        data = self.params({'title': ''})
        response = self.client.post('/dashboards/uuid', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Title cannot be blank'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_dashboard_description_field_is_required(self, mock_get_dashboard):
        data = self.params({'description': ''})
        response = self.client.post('/dashboards/uuid', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(
            response.data, contains_string('Description cannot be blank'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_dashboard_is_updated(
            self, mock_update_dashboard, mock_get_dashboard):
        data = self.params()
        self.client.post('/dashboards/uuid', data=data)
        post_json = mock_update_dashboard.call_args[0][1]
        assert_that(mock_update_dashboard.call_args[0][0], equal_to('uuid'))
        assert_that(post_json, has_entries(data))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_link_for_previewing_the_dashboard(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        url = '{0}/performance/valid-slug'.format(app.config['GOVUK_SITE_URL'])
        assert_that(response.data, contains_string(url))


class DashboardListTestCase(FlaskAppTestCase):

    def setUp(self):
        self.app = app.test_client()
        self.dashboards = {'dashboards': [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]}

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_dashboards_page_shows_a_list_of_dashboards(
            self, get_patch, client):
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response

        resp = client.get('/dashboards')

        assert_that(resp.data, contains_string('Name of service'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_dashboard_status_is_unpublished(self, get_patch, client):
        self.dashboards['dashboards'][0]['published'] = False
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response

        resp = client.get('/dashboards')

        assert_that(resp.data, contains_string('Unpublished'))

    @signed_in(permissions=['signin'])
    def test_authorised_user_is_required(self, client):
        resp = client.get('/dashboards')
        assert_that(resp.status, equal_to('302 FOUND'))

    def test_authenticated_user_is_required(self):
        resp = self.client.get('/dashboards')
        assert_that(resp.status, equal_to('302 FOUND'))
