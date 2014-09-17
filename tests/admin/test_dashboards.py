from tests.admin.support.flask_app_test_case import FlaskAppTestCase
from admin import app
from hamcrest import assert_that, contains_string, ends_with, equal_to
from mock import patch, Mock

import json
import requests


class DashboardTestCase(FlaskAppTestCase):
    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

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

    @patch("requests.post")
    def test_create_post_sends_a_post_to_stagecraft(self, post_patch):
        successful_post = requests.Response()
        successful_post.status_code = 200
        post_patch.return_value = successful_post

        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'dashboard']
                }

            resp = admin_app.post('/administer-dashboards/create',
                                  data={'slug': 'valid-slug'})

        post_headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer token',
        }
        post_json = json.loads(post_patch.call_args[1]['data'])

        assert_that(post_patch.call_args[0][0], ends_with('/dashboard'))
        assert_that(post_patch.call_args[1]['headers'], equal_to(post_headers))
        assert_that(post_json['slug'], equal_to('valid-slug'))
        assert_that(resp.status_code, equal_to(302))

    @patch("requests.post")
    def test_creating_dashboard_deletes_from_session(self, post_patch):
        successful_post = requests.Response()
        successful_post.status_code = 200
        post_patch.return_value = successful_post

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

    @patch("requests.post")
    def test_failed_dashboard_creation_stored_in_session(self, post_patch):
        response_json_mock = Mock()
        response_json_mock.return_value = {'message': 'Error message'}
        successful_post = requests.Response()
        successful_post.status_code = 400
        successful_post.json = response_json_mock
        post_patch.return_value = successful_post

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
