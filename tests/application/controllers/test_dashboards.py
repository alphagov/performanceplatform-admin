from tests.application.support.flask_app_test_case import (
    FlaskAppTestCase
)
from mock import patch
from application import app
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    has_entries,
    ends_with,
    not_none,
    match_equality
)
import os
import json


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
                'permissions': ['signin', 'dashboard-editor']
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
    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_dashboard_is_updated(
            self, mock_update_dashboard, mock_get_dashboard):
        data = self.params()
        response = self.client.post('/dashboards/dashboard-uuid', data=data)
        post_json = mock_update_dashboard.call_args[0][1]
        assert_that(
            mock_update_dashboard.call_args[0][0], equal_to('dashboard-uuid'))
        assert_that(post_json, has_entries(data))
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/dashboards/dashboard-uuid'))
        self.assert_flashes(
            'Your dashboard has been updated', 'success')

    @patch("application.controllers.dashboards.render_template")
    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    def test_doesnt_render_templates_with_modules_without_data_type(
            self,
            mock_get_dashboard,
            mock_render_template):
        mock_render_template.return_value = ''
        mock_get_dashboard.return_value = dashboard_data(
            {'modules': [
                {'slug': 'slug'},
                {'data_type': 'user-satisfaction-score'}]})
        self.client.get('/dashboards/dashboard-uuid')
        mock_render_template.assert_called_once_with(
            match_equality('builder/dashboard-hub.html'),
            dashboard_title=match_equality(not_none()),
            uuid=match_equality(not_none()),
            form=match_equality(not_none()),
            modules=match_equality(['user-satisfaction-score']),
            preview_url=match_equality(not_none()),
            environment=match_equality(not_none()),
            user=match_equality(not_none()),
        )
        # mock_render_template.assert_called_once_with('abc')

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

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    def test_advises_digital_take_up_has_been_added(self, mock_get_dashboard):
        mock_get_dashboard.return_value = dashboard_data(
            {'modules': [{'data_type': 'user-satisfaction-score'}]})
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.data, contains_string('Data successfully set up'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_section_for_user_satisfaction(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(
            response.data, contains_string('<h1>User satisfaction</h1>'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    def test_renders_a_link_to_add_user_satisfaction(
            self, mock_get_dashboard):
        response = self.client.get('/dashboards/dashboard-uuid')
        url = '/dashboard-uuid/user-satisfaction/add'
        assert_that(response.data, contains_string(url))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    def test_advises_user_satisfaction_has_been_added(
            self, mock_get_dashboard):
        mock_get_dashboard.return_value = dashboard_data(
            {'modules': [{'data_type': 'user-satisfaction-score'}]})
        response = self.client.get('/dashboards/dashboard-uuid')
        assert_that(response.data, contains_string('Data successfully set up'))

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

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data())
    @patch("performanceplatform.client.admin.AdminAPI.delete_dashboard")
    def test_delete_unpublished_dashboard(
            self, mock_delete_dashboard, mock_get_dashboard):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']}
        response = self.client.delete('/delete/dashboard-uuid')
        self.assert_flashes('A dashboard deleted', 'info')
        assert_that(response.status, equal_to('302 FOUND'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard",
           return_value=dashboard_data(
               {'status': ' published', 'published': True}))
    @patch("performanceplatform.client.admin.AdminAPI.delete_dashboard")
    def test_delete_published_dashboard(
            self, mock_delete_dashboard, mock_get_dashboard):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']}
        response = self.client.delete('/delete/dashboard-uuid')
        self.assert_flashes('Cannot delete published dashboard', 'info')
        assert_that(response.status, equal_to('302 FOUND'))


class SendDashboardForReviewTestCase(FlaskAppTestCase):

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard-editor'],
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
        self.dashboards = [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'status': 'published',
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]

        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard-editor']
            }

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {
                'permissions': ['signin']}
        resp = self.client.get('/dashboards')
        assert_that(resp.status, equal_to('302 FOUND'))

    def test_authenticated_user_is_required(self):
        with self.client.session_transaction() as session:
            del session['oauth_token']
        resp = self.client.get('/dashboards')
        assert_that(resp.status, equal_to('302 FOUND'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_index_page_shows_a_list_of_dashboards(
            self, get_patch):
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        assert_that(resp.data, contains_string('Name of service'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_index_page_with_stagecraft_0_dashboards_shows_errors(
            self, get_patch):

        get_patch.return_value.status_code = 200

        resp = self.client.get('/dashboards')

        assert_that(resp.data, contains_string(
            'No dashboards stored'
        ))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_index_page_with_stagecraft_down_shows_errors(
            self, get_patch):
        get_patch.return_value = None

        resp = self.client.get('/dashboards')

        assert_that(resp.data, contains_string(
            'Could not retrieve the list of dashboards'
        ))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_published_dashboards_are_flagged_as_published(
            self, get_patch):
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        assert_that(resp.data, contains_string('Published'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_unpublished_dashboards_are_flagged_as_unpublished(
            self, get_patch):
        self.dashboards[0]['status'] = 'unpublished'
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        assert_that(resp.data, contains_string('Unpublished'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_in_review_dashboards_are_flagged_as_in_review(
            self, get_patch):
        self.dashboards[0]['status'] = 'in-review'
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        assert_that(resp.data, contains_string('In Review'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_published_dashboards_cannot_be_edited(
            self, get_patch):
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        self.assertFalse('Edit dashboard' in resp.data)

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_unpublished_dashboards_can_be_edited(
            self, get_patch):

        self.dashboards[0]['status'] = 'unpublished'
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        assert_that(resp.data, contains_string('Edit dashboard'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboards")
    def test_in_review_dashboards_cannot_be_edited(
            self, get_patch):
        self.dashboards[0]['status'] = 'in-review'
        get_patch.return_value = self.dashboards
        resp = self.client.get('/dashboards')
        self.assertFalse('Edit dashboard' in resp.data)
