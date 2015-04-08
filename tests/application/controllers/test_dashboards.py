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
    has_entries,
    ends_with
)
import os
import json
import requests


def dashboard_data(options={}):
    params = {
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
        'status': 'unpublished'
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
           return_value=dashboard_data({'status': 'in-review'}))
    def test_in_review_dashboards_cannot_be_edited(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        self.assert_flashes(
            'In review or published dashboards cannot be edited', 'info')
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/dashboards'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data({'status': 'published'}))
    def test_published_dashboards_cannot_be_edited(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        self.assert_flashes(
            'In review or published dashboards cannot be edited', 'info')
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/dashboards'))

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
        response = self.client.post('/dashboards/dashboard-uuid', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Title cannot be blank'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_dashboard_description_field_is_required(self, mock_get_dashboard):
        data = self.params({'description': ''})
        response = self.client.post('/dashboards/dashboard-uuid', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(
            response.data, contains_string('Description cannot be blank'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_section_for_digital_take_up(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.data, contains_string('<h1>Digital take-up</h1>'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_link_to_add_digital_take_up(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        url = '/dashboard-uuid/digital-take-up/upload-options'
        assert_that(response.data, contains_string(url))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_dashboard_is_updated(
            self, mock_update_dashboard, mock_get_dashboard):
        data = self.params()
        self.client.post('/dashboards/dashboard-uuid', data=data)
        post_json = mock_update_dashboard.call_args[0][1]
        assert_that(
            mock_update_dashboard.call_args[0][0], equal_to('dashboard-uuid'))
        assert_that(post_json, has_entries(data))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_link_for_previewing_the_dashboard(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        url = '{0}/performance/valid-slug'.format(app.config['GOVUK_SITE_URL'])
        assert_that(response.data, contains_string(url))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_button_for_sending_unpublished_dashboards_for_review(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.data,
                    contains_string('Send dashboard for review'))


class SendDashboardForReviewTestCase(FlaskAppTestCase):

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard'],
                'name': 'Mr Foo Bar',
                'email': 'foo@bar.com'
            }

    def test_authenticated_user_is_required(self):
        with self.client.session_transaction() as session:
            del session['oauth_token']
        response = self.client.post(
            '/dashboards/dashboard-uuid/send-for-review',
            data={})
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.post(
            '/dashboards/dashboard-uuid/send-for-review',
            data={})
        assert_that(response.status, equal_to('302 FOUND'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    @patch("boto.ses.connect_to_region")
    def test_dashboard_status_is_changed_to_in_review(
            self,
            mock_ses_connection,
            mock_update_dashboard,
            mock_get_dashboard):
        self.client.post('/dashboards/dashboard-uuid/send-for-review', data={})
        post_json = mock_update_dashboard.call_args[0][1]
        assert_that(
            mock_update_dashboard.call_args[0][0], equal_to('dashboard-uuid'))
        data = {'status': 'in-review'}
        assert_that(post_json, has_entries(data))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    @patch("boto.ses.connect_to_region")
    def test_sends_review_dashboard_request_by_email(
            self,
            mock_ses_connection,
            mock_update_dashboard,
            mock_get_dashboard):
        self.client.post('/dashboards/dashboard-uuid/send-for-review', data={})
        second_call_args = mock_ses_connection.mock_calls[1][1]
        assert_that(second_call_args[0],
                    equal_to(app.config['NO_REPLY_EMAIL']))
        assert_that(second_call_args[1],
                    equal_to('Request to review a dashboard'))
        assert_that(second_call_args[2], contains_string('Mr Foo Bar'))
        assert_that(
            second_call_args[2], contains_string('foo@bar.com'))
        assert_that(second_call_args[2], contains_string('A dashboard'))
        assert_that(
            second_call_args[3],
            equal_to(app.config['NOTIFICATIONS_EMAIL']))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    @patch("boto.ses.connect_to_region")
    def test_redirects_to_about_your_service_page(
            self,
            mock_ses_connection,
            mock_update_dashboard,
            mock_get_dashboard):
        response = self.client.post(
            '/dashboards/dashboard-uuid/send-for-review', data={})
        self.assert_flashes(
            'Your dashboard has been sent for review', 'success')
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/dashboards'))


class DashboardListTestCase(FlaskAppTestCase):

    def setUp(self):
        self.app = app.test_client()
        self.dashboards = {'dashboards': [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'status': 'published',
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]}

    @signed_in(permissions=['signin'])
    def test_authorised_user_is_required(self, client):
        resp = client.get('/dashboards')
        assert_that(resp.status, equal_to('302 FOUND'))

    def test_authenticated_user_is_required(self):
        resp = self.client.get('/dashboards')
        assert_that(resp.status, equal_to('302 FOUND'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_index_page_shows_a_list_of_dashboards(
            self, get_patch, client):
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        assert_that(resp.data, contains_string('Name of service'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_index_page_with_stagecraft_down_or_0_dashboards_shows_errors(
            self, get_patch, client):
        response = requests.Response()
        response.status_code = 500
        get_patch.return_value = response

        resp = client.get('/dashboards')

        assert_that(resp.data, contains_string(
            'Could not retrieve the list of dashboards'
        ))

        response.status_code = 200
        response.json = Mock(return_value={'dashboards': []})
        get_patch.return_value = response

        resp = client.get('/dashboards')

        assert_that(resp.data, contains_string(
            'No dashboards stored'
        ))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_index_page_with_stagecraft_down_errors(self, get_patch, client):
        response = requests.Response()
        response.status_code = 500
        get_patch.return_value = response

        resp = client.get('/dashboards')

        assert_that(resp.data, contains_string(
            'Could not retrieve the list of dashboards'
        ))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_published_dashboards_are_flagged_as_published(
            self, get_patch, client):
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        assert_that(resp.data, contains_string('Published'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_unpublished_dashboards_are_flagged_as_unpublished(
            self, get_patch, client):
        self.dashboards['dashboards'][0]['status'] = 'unpublished'
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        assert_that(resp.data, contains_string('Unpublished'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_in_review_dashboards_are_flagged_as_in_review(
            self, get_patch, client):
        self.dashboards['dashboards'][0]['status'] = 'in-review'
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        assert_that(resp.data, contains_string('In Review'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_published_dashboards_cannot_be_edited(
            self, get_patch, client):
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        self.assertFalse('Edit dashboard' in resp.data)

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_unpublished_dashboards_can_be_edited(
            self, get_patch, client):
        self.dashboards['dashboards'][0]['status'] = 'unpublished'
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        assert_that(resp.data, contains_string('Edit dashboard'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_in_review_dashboards_cannot_be_edited(
            self, get_patch, client):
        self.dashboards['dashboards'][0]['status'] = 'in-review'
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=self.dashboards)
        get_patch.return_value = response
        resp = client.get('/dashboards')
        self.assertFalse('Edit dashboard' in resp.data)
