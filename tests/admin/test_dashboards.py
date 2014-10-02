from tests.admin.support.flask_app_test_case import FlaskAppTestCase
from admin import app
from hamcrest import (assert_that, contains_string, equal_to, has_entries,
                      ends_with, instance_of)
from mock import patch, Mock
from admin.forms import DashboardCreationForm

import requests
import os
import json


class DashboardTestCase(FlaskAppTestCase):
    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_creating_dashboard_with_a_module(self, create_dashboard):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'dashboard']
                }

            data = {
                'slug': 'my-valid-slug',
                'title': 'My valid title',
                'modules-0-slug': 'carers-realtime',
                'modules-0-data_group': 'carers-allowance',
                'modules-0-data_type': 'realtime',
                'modules-0-options': '{}',
                'modules-0-query_parameters': '{}',
            }

            admin_app.post('/administer-dashboards/create', data=data)

        post_json = create_dashboard.call_args[0][0]

        assert_that(post_json['modules'][0], has_entries({
            'slug': 'carers-realtime',
            'data_group': 'carers-allowance',
            'data_type': 'realtime',
            'options': {},
            'query_parameters': {},
        }))

    def test_create_form_uses_pending_dashboard_if_stored(self):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'dashboard']
                }
                session['pending_dashboard'] = {'slug': 'my-valid-slug'}

            resp = admin_app.get('/administer-dashboards/create')

            assert_that(resp.data, contains_string('value="my-valid-slug"'))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_create_post_sends_a_post_to_stagecraft(self, create_dashboard):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'dashboard']
                }

            resp = admin_app.post('/administer-dashboards/create',
                                  data={'slug': 'valid-slug'})

        post_json = create_dashboard.call_args[0][0]

        assert_that(post_json['slug'], equal_to('valid-slug'))
        assert_that(resp.status_code, equal_to(302))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_creating_dashboard_deletes_from_session(self, create_dashboard):
        dashboard_data = {
            'slug': 'valid-slug',
        }

        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard']
            }
            session['pending_dashboard'] = dashboard_data

        self.client.post('/administer-dashboards/create',
                         data=dashboard_data)

        self.assert_session_does_not_contain('pending_dashboard')
        self.assert_flashes('Created the valid-slug dashboard', 'success')

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_failed_dashboard_creation_stored_in_session(self,
                                                         create_dashboard):
        response_json_mock = Mock()
        response_json_mock.return_value = {'message': 'Error message'}
        response = requests.Response()
        response.status_code = 400
        response.json = response_json_mock
        error = requests.HTTPError('Error message', response=response)
        create_dashboard.side_effect = error

        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard']
            }

        self.client.post('/administer-dashboards/create',
                         data={'slug': 'foo'})

        self.assert_session_contains('pending_dashboard', {'slug': 'foo'})
        self.assert_flashes('Error creating the foo dashboard: Error message',
                            'danger')

    def test_add_module_redirects_back_to_the_form(self):
        dashboard_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
        }
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard']
            }
            session['pending_dashboard'] = dashboard_data

        resp = self.client.post('/administer-dashboards/create',
                                data={'add_module': 1})

        assert_that(resp.status_code, equal_to(302))

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_editing_existing_dashboard(self, update_mock):
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard']
            }
        data = {
            'slug': 'my-valid-slug',
            'title': 'My valid title',
            'modules-0-slug': 'carers-realtime',
            'modules-0-data_group': 'carers-allowance',
            'modules-0-data_type': 'realtime',
            'modules-0-options': '{}',
            'modules-0-query_parameters': '{}',
            'modules-0-id': 'module-uuid',
        }

        resp = self.client.post(
            '/administer-dashboards/update/uuid', data=data)
        post_json = update_mock.call_args[0][1]
        assert_that(post_json['modules'][0], has_entries({
            'slug': 'carers-realtime',
            'data_group': 'carers-allowance',
            'data_type': 'realtime',
            'options': {},
            'query_parameters': {},
            'id': 'module-uuid',
        }))
        assert_that(update_mock.call_args[0][0], equal_to('uuid'))
        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['Location'],
            ends_with('/administer-dashboards/edit/uuid'))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    @patch("admin.dashboards.render_template")
    def test_rendering_edit_page(self, mock_render, mock_get):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../fixtures/example-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        mock_render.return_value = ''
        mock_get.return_value = dashboard_dict
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'dashboard']
            }

        resp = self.client.get('/administer-dashboards/edit/uuid')
        mock_get.assert_called_once_with('uuid')
        rendered_template = 'dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        assert_that(kwargs['form'], instance_of(DashboardCreationForm))
        assert_that(resp.status_code, equal_to(200))
