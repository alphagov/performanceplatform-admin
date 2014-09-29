from tests.admin.support.flask_app_test_case import FlaskAppTestCase, signed_in
from admin import app
from hamcrest import assert_that, contains_string, equal_to, has_entries, \
    has_key, has_entry
from mock import patch, Mock

import requests


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

        self.assert_session_contains('pending_dashboard',
                                     has_entry('slug', 'foo'))
        self.assert_flashes('Error creating the foo dashboard: Error message',
                            'danger')

    @signed_in(permissions=['signin', 'dashboard'])
    def test_add_module_redirects_back_to_the_form(self, client):
        resp = client.post('/administer-dashboards/create',
                           data={'add_module': 1})

        assert_that(resp.status_code, equal_to(302))

    @signed_in(permissions=['signin', 'dashboard'])
    def test_remove_module_after_adding(self, client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'remove_module_0': 'remove',
        }

        client.post('/administer-dashboards/create',
                    data=form_data)

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

        client.post('/administer-dashboards/create',
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

        client.post('/administer-dashboards/create',
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

        client.post('/administer-dashboards/create',
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

        client.post('/administer-dashboards/create',
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

        client.post('/administer-dashboards/create',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard']['modules'][0],
                        has_entry('slug', 'foo'))
            assert_that(session['pending_dashboard']['modules'][1],
                        has_entry('slug', 'bar'))
