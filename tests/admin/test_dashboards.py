from tests.admin.support.flask_app_test_case import FlaskAppTestCase, signed_in
from admin import app
from hamcrest import (assert_that, contains_string, equal_to, has_entries,
                      ends_with, instance_of, has_key, has_entry)
from mock import patch, Mock
from admin.forms import DashboardCreationForm

import requests
import os
import json


class DashboardIndexTestCase(FlaskAppTestCase):
    def setUp(self):
        self.app = app.test_client()

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_index_page_shows_list_of_dashboards(self, get_patch, client):
        dashboards = {'dashboards': [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]}
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=dashboards)
        get_patch.return_value = response

        resp = client.get('/administer-dashboards')

        assert_that(resp.data, contains_string(
            '<li><a href="/administer-dashboards/uuid">'
            'Name of service</a></li>'
        ))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_index_page_with_stagecraft_down_or_0_dashboards_shows_errors(
            self, get_patch, client):
        response = requests.Response()
        response.status_code = 500
        get_patch.return_value = response

        resp = client.get('/administer-dashboards')

        assert_that(resp.data, contains_string(
            'Could not retrieve the list of dashboards'
        ))

        response.status_code = 200
        response.json = Mock(return_value={'dashboards': []})
        get_patch.return_value = response

        resp = client.get('/administer-dashboards')

        assert_that(resp.data, contains_string(
            'No dashboards stored'
        ))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('requests.get')
    def test_index_page_with_stagecraft_down_errors(self, get_patch, client):
        response = requests.Response()
        response.status_code = 500
        get_patch.return_value = response

        resp = client.get('/administer-dashboards')

        assert_that(resp.data, contains_string(
            'Could not retrieve the list of dashboards'
        ))


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
                'modules-0-info': '["Foo", "Bar"]',
            }

            admin_app.post('/administer-dashboards', data=data)

        post_json = create_dashboard.call_args[0][0]

        assert_that(post_json['modules'][0], has_entries({
            'slug': 'carers-realtime',
            'data_group': 'carers-allowance',
            'data_type': 'realtime',
            'options': {},
            'query_parameters': {},
            'info': ["Foo", "Bar"],
        }))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_info_many_paths(self, create_dashboard):
        info_tests = [
            ('asdas',   False, 'Not valid JSON'),
            ('{}',      False, 'Not an array'),
            ('[123]',   False, 'An array containing a non-string'),
            ('[]',      True,  'An empty list'),
            ('',        True,  'An empty field'),
            (' ',       True,  'Whitespace should be stripped'),
            ('["Foo"]', True,  'A list with a string'),
        ]
        for info, success, message in info_tests:
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
                    'modules-0-info': info
                }

                admin_app.post('/administer-dashboards', data=data)

                with admin_app.session_transaction() as session:
                    flash_status = session['_flashes'][0][0]
                    if success:
                        assert_that(flash_status, equal_to('success'), message)
                    else:
                        assert_that(flash_status, equal_to('danger'), message)
                    # reset flashes
                    session['_flashes'] = []

    def test_create_form_uses_pending_dashboard_if_stored(self):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'dashboard']
                }
                session['pending_dashboard'] = {'slug': 'my-valid-slug'}

            resp = admin_app.get('/administer-dashboards/new')

            assert_that(resp.data, contains_string('value="my-valid-slug"'))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_create_post_sends_a_post_to_stagecraft(self, create_dashboard):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'dashboard']
                }

            resp = admin_app.post('/administer-dashboards',
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

        self.client.post('/administer-dashboards',
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

        self.client.post('/administer-dashboards',
                         data={'slug': 'foo'})

        self.assert_session_contains('pending_dashboard',
                                     has_entry('slug', 'foo'))
        self.assert_flashes('Error creating the foo dashboard: Error message',
                            'danger')

    @signed_in(permissions=['signin', 'dashboard'])
    def test_add_module_redirects_back_to_the_form(self, client):
        resp = client.post('/administer-dashboards',
                           data={'add_module': 1})

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['location'],
            contains_string('administer-dashboards/new?modules=1')
        )

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_updating_existing_dashboard(self, update_mock):
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
            '/administer-dashboards/uuid', data=data)
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
            ends_with('/administer-dashboards'))
        self.assert_flashes(
            'Updated the my-valid-slug dashboard', expected_category='success')

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_failing_updating_existing_dashboard_flashes_error(
            self, update_mock):
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
        response_json_mock = Mock()
        response_json_mock.return_value = {'message': 'Error message'}
        response = requests.Response()
        response.status_code = 400
        response.json = response_json_mock
        error = requests.HTTPError('Error message', response=response)
        update_mock.side_effect = error

        resp = self.client.post(
            '/administer-dashboards/uuid', data=data)
        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['Location'],
            ends_with('/administer-dashboards/uuid'))
        self.assert_flashes(
            'Error updating the my-valid-slug dashboard: Error message',
            expected_category='danger')

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

        resp = self.client.get('/administer-dashboards/uuid')
        mock_get.assert_called_once_with('uuid')
        rendered_template = 'dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        assert_that(kwargs['form'], instance_of(DashboardCreationForm))
        assert_that(resp.status_code, equal_to(200))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_remove_module_after_adding(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'remove_module_0': 'remove',
        }

        client.post('/administer-dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard'],
                        has_key('slug'))
            assert_that(len(session['pending_dashboard']['modules']),
                        equal_to(0))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_remove_module_from_existing_dashboard(self, client):
        data = {
            'slug': 'my-valid-slug',
            'title': 'My valid title',
            'modules-0-slug': 'carers-realtime',
            'modules-0-data_group': 'carers-allowance',
            'modules-0-data_type': 'realtime',
            'modules-0-options': '{}',
            'modules-0-query_parameters': '{}',
            'modules-0-id': 'module-uuid',
            'remove_module_0': 'remove',
        }

        client.post(
            '/administer-dashboards/uuid', data=data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard'],
                        has_key('slug'))
            assert_that(len(session['pending_dashboard']['modules']),
                        equal_to(0))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_remove_middle_module(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'remove_module_0': 'remove',
        }

        client.post('/administer-dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(len(session['pending_dashboard']['modules']),
                        equal_to(1))
            assert_that(session['pending_dashboard']['modules'][0]['slug'],
                        equal_to('bar'))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_move_first_module_down(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'move_module_down_0': 'move',
        }

        client.post('/administer-dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard']['modules'][0],
                        has_entry('slug', 'bar'))
            assert_that(session['pending_dashboard']['modules'][1],
                        has_entry('slug', 'foo'))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_move_last_module_down(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'move_module_down_1': 'move',
        }

        client.post('/administer-dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard']['modules'][0],
                        has_entry('slug', 'foo'))
            assert_that(session['pending_dashboard']['modules'][1],
                        has_entry('slug', 'bar'))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_move_last_module_down_on_existing_dashboard(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'move_module_down_1': 'move',
        }

        client.post('/administer-dashboards/uuid',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard']['modules'][0],
                        has_entry('slug', 'foo'))
            assert_that(session['pending_dashboard']['modules'][1],
                        has_entry('slug', 'bar'))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_move_last_module_up(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'move_module_up_1': 'move',
        }

        client.post('/administer-dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard']['modules'][0],
                        has_entry('slug', 'bar'))
            assert_that(session['pending_dashboard']['modules'][1],
                        has_entry('slug', 'foo'))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_move_first_module_up(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'move_module_up_0': 'move',
        }

        client.post('/administer-dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard']['modules'][0],
                        has_entry('slug', 'foo'))
            assert_that(session['pending_dashboard']['modules'][1],
                        has_entry('slug', 'bar'))
