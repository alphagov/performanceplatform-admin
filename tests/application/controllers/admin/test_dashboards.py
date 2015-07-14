from tests.application.support.flask_app_test_case import (
    FlaskAppTestCase, signed_in)
from application import app
from hamcrest import (assert_that, contains_string, equal_to, has_entries,
                      ends_with, instance_of, has_key, has_entry)
from mock import patch, Mock
from application.forms import DashboardCreationForm

import requests
import os
import json


def module_types_list():
    return [{'id': 'availability-module-type-uuid', 'name': 'availability'},
            {'id': 'section-module-type-uuid', 'name': 'section'}]


def data_sets_list():
    with open(os.path.join(
              os.path.dirname(__file__),
              '../../../fixtures/data-sets-extract.json')) as file:
        data_sets_json = file.read()
    return json.loads(data_sets_json)


def organisations_list():
    return [{'id': 'organisation-uuid', 'name': 'Mock organisation'}]


def valid_dashboard_data(options=None):
    data = {
        'slug': 'valid-slug',
        'title': 'My valid title',
        'owning_organisation': 'organisation-uuid',
        'dashboard_type': 'transaction',
        'customer_type': 'Business',
        'strapline': 'Dashboard',
        'business_model': 'Department budget'
    }
    if options:
        data.update(options)
    return data


@patch("performanceplatform.client.admin.AdminAPI.list_module_types",
       return_value=module_types_list())
@patch("performanceplatform.client.admin.AdminAPI.list_data_sets",
       return_value=data_sets_list())
@patch("performanceplatform.client.admin.AdminAPI.list_organisations",
       return_value=organisations_list())
class DashboardTestCase(FlaskAppTestCase):

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_creating_dashboard_with_a_module(self,
                                              create_dashboard,
                                              mock_list_organisations,
                                              mock_list_data_sets,
                                              mock_list_module_types):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'admin']
                }

            data = valid_dashboard_data({
                'modules-0-module_type': '',
                'modules-0-slug': 'carers-realtime',
                'modules-0-data_group': 'carers-allowance',
                'modules-0-data_type': 'realtime',
                'modules-0-options': '{}',
                'modules-0-query_parameters': '{}',
                'modules-0-info': '["Foo", "Bar"]'
            })

            admin_app.post('/admin/dashboards', data=data)

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
    def test_creating_a_dashboard_with_a_sectioned_module(
            self,
            create_dashboard,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'admin']
                }

            data = valid_dashboard_data({
                'modules-0-module_type': 'availability-module-type-uuid',
                'modules-0-slug': 'carers-realtime-1',
                'modules-0-data_group': 'carers-allowance',
                'modules-0-data_type': 'realtime',
                'modules-0-options': '{}',
                'modules-0-query_parameters': '{}',
                'modules-0-info': '["Foo", "Bar"]',
                'modules-1-module_type': 'section-module-type-uuid',
                'modules-1-category': 'container',
                'modules-1-slug': 'section-1',
                'modules-1-title': 'Section 1 title',
                'modules-1-description': 'Section description',
                'modules-2-module_type': 'availability-module-type-uuid',
                'modules-2-slug': 'carers-realtime-2',
                'modules-2-data_group': 'carers-allowance',
                'modules-2-data_type': 'realtime',
                'modules-2-options': '{}',
                'modules-2-query_parameters': '{}',
                'modules-2-info': '["Foo", "Bar"]',
                'modules-3-module_type': 'availability-module-type-uuid',
                'modules-3-slug': 'carers-realtime-3',
                'modules-3-data_group': 'carers-allowance',
                'modules-3-data_type': 'realtime',
                'modules-3-options': '{}',
                'modules-3-query_parameters': '{}',
                'modules-3-info': '["Foo", "Bar"]',
                'modules-4-module_type': 'section-module-type-uuid',
                'modules-4-category': 'container',
                'modules-4-slug': 'section-2',
                'modules-4-title': 'Section 2 title',
                'modules-4-description': 'Section description'
            })

            admin_app.post('/admin/dashboards', data=data)

        post_json = create_dashboard.call_args[0][0]

        assert_that(post_json['modules'][1], has_entries({
            'slug': 'section-1',
            'order': 2
        }))

        assert_that(post_json['modules'][1]['modules'][0], has_entries({
            'slug': 'carers-realtime-2',
            'order': 3
        }))

        assert_that(post_json['modules'][1]['modules'][1], has_entries({
            'slug': 'carers-realtime-3',
            'order': 4
        }))

        assert_that(post_json['modules'][2], has_entries({
            'slug': 'section-2',
            'order': 5
        }))

    def test_creating_dashboard_without_organisation(self,
                                                     mock_list_organisations,
                                                     mock_list_data_sets,
                                                     mock_list_module_types):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'admin']
                }

            data = valid_dashboard_data({'owning_organisation': ''})

            resp = admin_app.post('/admin/dashboards', data=data)

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['Location'],
            ends_with('/admin/dashboards/new'))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_info_many_paths(self,
                             create_dashboard,
                             mock_list_organisations,
                             mock_list_data_sets,
                             mock_list_module_types):
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
                        'permissions': ['signin', 'admin']
                    }

                data = valid_dashboard_data({
                    'modules-0-module_type': '',
                    'modules-0-slug': 'carers-realtime',
                    'modules-0-data_group': 'carers-allowance',
                    'modules-0-data_type': 'realtime',
                    'modules-0-options': '{}',
                    'modules-0-query_parameters': '{}',
                    'modules-0-info': info
                })

                admin_app.post('/admin/dashboards', data=data)

                with admin_app.session_transaction() as session:
                    flash_status = session['_flashes'][0][0]
                    if success:
                        assert_that(flash_status, equal_to('success'), message)
                    else:
                        assert_that(flash_status, equal_to('danger'), message)
                    # reset flashes
                    session['_flashes'] = []

    def test_create_form_uses_pending_dashboard_if_stored(
            self,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'admin']
                }
                session['pending_dashboard'] = {'slug': 'my-valid-slug'}

            resp = admin_app.get('/admin/dashboards/new')

            assert_that(resp.data, contains_string('value="my-valid-slug"'))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_create_post_sends_a_post_to_stagecraft(self,
                                                    create_dashboard,
                                                    mock_list_organisations,
                                                    mock_list_data_sets,
                                                    mock_list_module_types):
        with self.app as admin_app:
            with admin_app.session_transaction() as session:
                session['oauth_token'] = {'access_token': 'token'}
                session['oauth_user'] = {
                    'permissions': ['signin', 'admin']
                }

            data = valid_dashboard_data()

            resp = admin_app.post('/admin/dashboards', data=data)

        post_json = create_dashboard.call_args[0][0]

        assert_that(post_json['slug'], equal_to('valid-slug'))
        assert_that(resp.status_code, equal_to(302))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_creating_dashboard_deletes_from_session(self,
                                                     create_dashboard,
                                                     mock_list_organisations,
                                                     mock_list_data_sets,
                                                     mock_list_module_types):
        dashboard_data = {
            'slug': 'valid-slug',
        }

        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }
            session['pending_dashboard'] = dashboard_data

        self.client.post('/admin/dashboards',
                         data=valid_dashboard_data())

        self.assert_session_does_not_contain('pending_dashboard')
        self.assert_flashes('Created the valid-slug dashboard', 'success')

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_failed_dashboard_creation_stored_in_session(
            self,
            create_dashboard,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types):
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
                'permissions': ['signin', 'admin']
            }

        self.client.post('/admin/dashboards',
                         data=valid_dashboard_data())

        self.assert_session_contains('pending_dashboard',
                                     has_entry('slug', 'valid-slug'))
        self.assert_flashes(
            'Error creating the valid-slug dashboard: Error message',
            'danger'
        )

    @signed_in(permissions=['signin', 'admin'])
    def test_add_module_redirects_back_to_the_form(self,
                                                   mock_list_organisations,
                                                   mock_list_data_sets,
                                                   mock_list_module_types,
                                                   client):
        resp = client.post('/admin/dashboards',
                           data={'add_module': 1})

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['location'],
            contains_string('admin/dashboards/new?modules=1')
        )

    @signed_in(permissions=['signin', 'admin'])
    def test_clone_module_new_dashboard_redirects_with_correct_query_params(
            self,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        resp = client.post('/admin/dashboards',
                           data={'clone_module': 1})

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['location'],
            ends_with('/clone_module'))

    @signed_in(permissions=['signin', 'admin'])
    def test_clone_module_existing_dashboard_redirects_correct_query_params(
            self,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        dashboard_id = "def123abc"
        resp = client.post('/admin/dashboards/{}'.format(dashboard_id),
                           data={'clone_module': 1})

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['location'],
            ends_with('/clone_module/{}'
                      .format(dashboard_id))
        )

    @patch("performanceplatform.client.admin.AdminAPI.get_module")
    @patch("application.controllers.admin.dashboards.render_template")
    @signed_in(permissions=['signin', 'admin'])
    def test_clone_module_appends_to_the_form_with_the_correct_modules(
            self,
            mock_render,
            mock_get_module,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../../../fixtures/example-dashboard.json')) as file:
            module_dict = json.loads(file.read())['modules'][0]
        mock_render.return_value = ''
        mock_get_module.return_value = module_dict
        module_id = "abc123def"
        resp = client.get(
            'admin/dashboards/new?clone_module={}'.format(module_id))

        rendered_template = 'admin/dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        form = kwargs['form']
        modules = form.modules
        assert_that(len(modules), equal_to(1))
        cloned_module = form.modules[0]
        assert_that(
            cloned_module['id'].data, equal_to(None))
        assert_that(
            cloned_module['module_type'].data, equal_to(
                module_dict['module_type']))
        assert_that(
            cloned_module['data_group'].data, equal_to(
                module_dict['data_group']))
        assert_that(
            cloned_module['data_type'].data, equal_to(
                module_dict['data_type']))
        assert_that(
            cloned_module['slug'].data, equal_to(module_dict['slug']))
        assert_that(
            cloned_module['title'].data, equal_to(module_dict['title']))
        assert_that(
            cloned_module['description'].data, equal_to(
                module_dict['description']))
        assert_that(
            cloned_module['info'].data, equal_to(module_dict['info']))
        assert_that(
            cloned_module['query_parameters'].data, equal_to(
                module_dict['query_parameters']))
        assert_that(
            cloned_module['options'].data, equal_to(module_dict['options']))
        assert_that(resp.status_code, equal_to(200))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    @patch("performanceplatform.client.admin.AdminAPI.get_module")
    @patch("application.controllers.admin.dashboards.render_template")
    @signed_in(permissions=['signin', 'admin'])
    def test_clone_module_appends_correct_modules_to_form_existing_dashboard(
            self,
            mock_render,
            mock_get_module,
            mock_get_dashboard,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        dashboard_id = "def123abc"
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../../../fixtures/example-dashboard.json')) as file:
            dashboard_dict = json.loads(file.read())
            module_dict = dashboard_dict['modules'][0].copy()
        mock_render.return_value = ''
        mock_get_module.return_value = module_dict
        mock_get_dashboard.return_value = dashboard_dict
        module_id = "abc123def"
        # modules are seven because there is a section in the example data
        resp = client.get(
            'admin/dashboards/{}?clone_module={}'.format(
                dashboard_id, module_id))

        rendered_template = 'admin/dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        form = kwargs['form']
        modules = form.modules
        assert_that(len(modules), equal_to(7))
        cloned_module = form.modules[-1]
        assert_that(
            cloned_module['id'].data, equal_to(None))
        assert_that(
            cloned_module['module_type'].data, equal_to(
                module_dict['module_type']))
        assert_that(
            cloned_module['data_group'].data, equal_to(
                module_dict['data_group']))
        assert_that(
            cloned_module['data_type'].data, equal_to(
                module_dict['data_type']))
        assert_that(
            cloned_module['slug'].data, equal_to(module_dict['slug']))
        assert_that(
            cloned_module['title'].data, equal_to(module_dict['title']))
        assert_that(
            cloned_module['description'].data, equal_to(
                module_dict['description']))
        assert_that(
            cloned_module['info'].data, equal_to(module_dict['info']))
        assert_that(
            cloned_module['query_parameters'].data, equal_to(
                module_dict['query_parameters']))
        assert_that(
            cloned_module['options'].data, equal_to(module_dict['options']))
        assert_that(resp.status_code, equal_to(200))

    @patch('requests.get')
    @patch("application.controllers.admin.dashboards.render_template")
    @signed_in(permissions=['signin', 'admin'])
    def test_get_clone_module_no_target_uuid_renders_with_correct_args(
            self,
            mock_render,
            get_patch,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        mock_render.return_value = ''
        dashboards = [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=dashboards)
        get_patch.return_value = response
        client.get(
            'admin/dashboards/clone_module')
        rendered_template = 'dashboards/clone_module.html'
        mock_render.assert_called_once_with(
            rendered_template,
            modules=None,
            dashboards=dashboards,
            source_dashboard_uuid=None,
            selected_dashboard=None,
            target_dashboard_uuid=None,
            target_dashboard_name='new dashboard',
            user={'permissions': ['signin', 'admin']},
            environment={'human_name': 'Development', 'name': 'development'},
            target_dashboard_url='/admin/dashboards/new')

    @patch('requests.get')
    @patch("application.controllers.admin.dashboards.render_template")
    @signed_in(permissions=['signin', 'admin'])
    def test_get_clone_module_with_target_uuid_renders_with_correct_args(
            self,
            mock_render,
            get_patch,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        with client.session_transaction() as session:
            session['pending_dashboard'] = {
                'title': 'Dashboard title!'
            }
        mock_render.return_value = ''
        dashboards = [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]
        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=dashboards)
        get_patch.return_value = response
        client.get(
            'admin/dashboards/clone_module/target_dashboard_uuid')
        rendered_template = 'dashboards/clone_module.html'
        mock_render.assert_called_once_with(
            rendered_template,
            modules=None,
            dashboards=dashboards,
            source_dashboard_uuid=None,
            selected_dashboard=None,
            target_dashboard_uuid='target_dashboard_uuid',
            target_dashboard_name='Dashboard title!',
            user={'permissions': ['signin', 'admin']},
            environment={'human_name': 'Development', 'name': 'development'},
            target_dashboard_url='/admin/dashboards/target_dashboard_uuid')

    @patch('requests.get')
    @patch("application.controllers.admin.dashboards.render_template")
    @patch(
        "performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard")
    @signed_in(permissions=['signin', 'admin'])
    def test_post_clone_module_no_target_uuid_renders_with_correct_args(
            self,
            mock_list_modules_on_dashboard,
            mock_render,
            get_patch,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        mock_render.return_value = ''
        dashboards = [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]
        modules = [
            {
                'id': 'abc',
                'title': 'def'
            }
        ]

        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=dashboards)
        get_patch.return_value = response

        mock_list_modules_on_dashboard.return_value = modules

        client.post(
            'admin/dashboards/clone_module',
            data={'dashboard_uuid': 'uuid'})
        rendered_template = 'dashboards/clone_module.html'
        mock_render.assert_called_once_with(
            rendered_template,
            modules=[{'id': 'abc', 'title': 'def'}],
            dashboards=dashboards,
            source_dashboard_uuid='uuid',
            selected_dashboard=dashboards[0],
            target_dashboard_uuid=None,
            target_dashboard_name='new dashboard',
            user={'permissions': ['signin', 'admin']},
            environment={'human_name': 'Development', 'name': 'development'},
            target_dashboard_url='/admin/dashboards/new')

    @patch('requests.get')
    @patch("application.controllers.admin.dashboards.render_template")
    @patch(
        "performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard")
    @signed_in(permissions=['signin', 'admin'])
    def test_post_clone_module_with_target_uuid_renders_with_correct_args(
            self,
            mock_list_modules_on_dashboard,
            mock_render,
            get_patch,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        with client.session_transaction() as session:
            session['pending_dashboard'] = {
                'title': 'Dashboard title!'
            }
        mock_render.return_value = ''
        dashboards = [
            {
                'url': 'http://stagecraft/dashboard/uuid',
                'public-url': 'http://spotlight/performance/carers-allowance',
                'published': True,
                'id': 'uuid',
                'title': 'Name of service'
            }
        ]
        modules = [
            {
                'id': 'abc',
                'title': 'def'
            }
        ]

        response = requests.Response()
        response.status_code = 200
        response.json = Mock(return_value=dashboards)
        get_patch.return_value = response

        mock_list_modules_on_dashboard.return_value = modules

        client.post(
            'admin/dashboards/clone_module/target_dashboard_uuid',
            data={'dashboard_uuid': 'uuid'})
        rendered_template = 'dashboards/clone_module.html'
        mock_render.assert_called_once_with(
            rendered_template,
            modules=[{'id': 'abc', 'title': 'def'}],
            dashboards=dashboards,
            source_dashboard_uuid='uuid',
            selected_dashboard=dashboards[0],
            target_dashboard_uuid='target_dashboard_uuid',
            target_dashboard_name='Dashboard title!',
            user={'permissions': ['signin', 'admin']},
            environment={'human_name': 'Development', 'name': 'development'},
            target_dashboard_url='/admin/dashboards/target_dashboard_uuid')

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_updating_existing_dashboard(self,
                                         update_mock,
                                         mock_list_organisations,
                                         mock_list_data_sets,
                                         mock_list_module_types):
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        data = valid_dashboard_data({
            'modules-0-module_type': '',
            'modules-0-slug': 'carers-realtime',
            'modules-0-data_group': 'carers-allowance',
            'modules-0-data_type': 'realtime',
            'modules-0-options': '{}',
            'modules-0-query_parameters': '{}',
            'modules-0-id': 'module-uuid'
        })

        resp = self.client.post(
            '/admin/dashboards/uuid', data=data)
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
            ends_with('/dashboards'))
        expected_flash = 'Updated the <a href="http://spotlight.development' +\
            '.performance.service.gov.uk/performance/valid-slug">' + \
            'My valid title</a> dashboard'
        self.assert_flashes(expected_flash, expected_category='success')

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_save_and_continue_button_for_update(self,
                                                 update_mock,
                                                 mock_list_organisations,
                                                 mock_list_data_sets,
                                                 mock_list_module_types):
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        data = valid_dashboard_data({
            'save_and_continue':'',
        })

        resp = self.client.post(
            '/admin/dashboards/uuid', data=data)

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['Location'],
            ends_with('/admin/dashboards/uuid'))
        expected_flash = 'Updated the <a href="http://spotlight.development' +\
            '.performance.service.gov.uk/performance/valid-slug">' + \
            'My valid title</a> dashboard'
        self.assert_flashes(expected_flash, expected_category='success')

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    def test_save_and_continue_button_for_create(self,
                                                 create_dashboard,
                                                 mock_list_organisations,
                                                 mock_list_data_sets,
                                                 mock_list_module_types):
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        data = valid_dashboard_data({
            'save_and_continue': '',
        })
        dashboard_id = 1234
        create_dashboard.return_value = {'id': dashboard_id}
        resp = self.client.post(
            '/admin/dashboards', data=data)

        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['Location'],
            ends_with('/admin/dashboards/{}'.format(dashboard_id)))

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_updating_flash_escapes_title_html(self,
                                               update_mock,
                                               mock_list_organisations,
                                               mock_list_data_sets,
                                               mock_list_module_types):
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        data = valid_dashboard_data({
            'title': 'Bad title<h1>boo</h1>'
        })

        self.client.post(
            '/admin/dashboards/uuid', data=data)
        expected_flash = 'Updated the <a href="http://spotlight.development' +\
            '.performance.service.gov.uk/performance/valid-slug">' + \
            'Bad title&lt;h1&gt;boo&lt;/h1&gt;</a> dashboard'
        self.assert_flashes(expected_flash, expected_category='success')

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    def test_failing_updating_existing_dashboard_flashes_error(
            self,
            update_mock,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types):
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        data = valid_dashboard_data({
            'modules-0-module_type': '',
            'modules-0-slug': 'carers-realtime',
            'modules-0-data_group': 'carers-allowance',
            'modules-0-data_type': 'realtime',
            'modules-0-options': '{}',
            'modules-0-query_parameters': '{}',
            'modules-0-id': 'module-uuid',
        })

        response_json_mock = Mock()
        response_json_mock.return_value = {'message': 'Error message'}
        response = requests.Response()
        response.status_code = 400
        response.json = response_json_mock
        error = requests.HTTPError('Error message', response=response)
        update_mock.side_effect = error

        resp = self.client.post(
            '/admin/dashboards/uuid', data=data)
        assert_that(resp.status_code, equal_to(302))
        assert_that(
            resp.headers['Location'],
            ends_with('/admin/dashboards/uuid'))
        self.assert_flashes(
            'Error updating the valid-slug dashboard: Error message',
            expected_category='danger')

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    @patch("application.controllers.admin.dashboards.render_template")
    def test_rendering_edit_page(self,
                                 mock_render,
                                 mock_get,
                                 mock_list_organisations,
                                 mock_list_data_sets,
                                 mock_list_module_types):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../../../fixtures/example-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        mock_render.return_value = ''
        mock_get.return_value = dashboard_dict
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        resp = self.client.get('/admin/dashboards/uuid')
        mock_get.assert_called_once_with('uuid')
        rendered_template = 'admin/dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        assert_that(kwargs['form'], instance_of(DashboardCreationForm))
        assert_that(resp.status_code, equal_to(200))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    @patch("application.controllers.admin.dashboards.render_template")
    def test_rendering_edit_page_for_dashboard_without_owning_organisation(
            self,
            mock_render,
            mock_get,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../../../fixtures/example-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        dashboard_dict['organisation'] = None
        mock_render.return_value = ''
        mock_get.return_value = dashboard_dict
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        resp = self.client.get('/admin/dashboards/uuid')
        mock_get.assert_called_once_with('uuid')
        rendered_template = 'admin/dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        assert_that(kwargs['form'], instance_of(DashboardCreationForm))
        assert_that(resp.status_code, equal_to(200))

    @patch("performanceplatform.client.admin.AdminAPI.get_dashboard")
    @patch("application.controllers.admin.dashboards.render_template")
    def test_clone_dashboard_renders_a_prefilled_create_page(
            self,
            mock_render,
            mock_get,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../../../fixtures/example-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        dashboard_dict['organisation'] = None
        mock_render.return_value = ''
        mock_get.return_value = dashboard_dict
        with self.client.session_transaction() as session:
            session['oauth_token'] = {'access_token': 'token'}
            session['oauth_user'] = {
                'permissions': ['signin', 'admin']
            }

        resp = self.client.get('/admin/dashboards/clone?uuid=uuid')
        mock_get.assert_called_once_with('uuid')
        rendered_template = 'admin/dashboards/create.html'
        assert_that(mock_render.call_args[0][0], equal_to(rendered_template))
        kwargs = mock_render.call_args[1]
        form = kwargs['form']
        assert_that(form, instance_of(DashboardCreationForm))
        assert_that(form.strapline.data, equal_to(dashboard_dict['strapline']))
        assert_that(form['title'].data, equal_to(''))
        assert_that(form['slug'].data, equal_to(''))
        assert_that(form['published'].data, equal_to(False))
        for m in form.modules:
            assert_that(m['id'].data, equal_to(''))
        assert_that(resp.status_code, equal_to(200))

    @signed_in(permissions=['signin', 'admin'])
    def test_remove_module_after_adding(
            self,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'remove_module_0': 'remove',
        }

        client.post('/admin/dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard'],
                        has_key('slug'))
            assert_that(len(session['pending_dashboard']['modules']),
                        equal_to(0))

    @signed_in(permissions=['signin', 'admin'])
    def test_remove_module_from_existing_dashboard(
            self,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
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
            '/admin/dashboards/uuid', data=data)

        with client.session_transaction() as session:
            assert_that(session['pending_dashboard'],
                        has_key('slug'))
            assert_that(len(session['pending_dashboard']['modules']),
                        equal_to(0))

    @signed_in(permissions=['signin', 'admin'])
    def test_remove_middle_module(
            self,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'remove_module_0': 'remove',
        }

        client.post('/admin/dashboards',
                    data=form_data)

        with client.session_transaction() as session:
            assert_that(len(session['pending_dashboard']['modules']),
                        equal_to(1))
            assert_that(session['pending_dashboard']['modules'][0]['slug'],
                        equal_to('bar'))

    @patch("performanceplatform.client.admin.AdminAPI.create_dashboard")
    @patch("application.forms.DashboardCreationForm.validate")
    @signed_in(permissions=['signin', 'admin'])
    def test_reorder_modules_on_new_applies_changes_when_form_is_valid(
            self,
            mock_validate,
            mock_create_dashboard,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'modules_order': '2,1',
        }
        mock_validate.return_value = True
        client.post('/admin/dashboards',
                    data=form_data)

        assert_that(len(mock_create_dashboard.call_args_list), equal_to(1))

        post_json = mock_create_dashboard.call_args[0][0]

        assert_that(post_json['modules'][0], has_entries({
            'slug': 'bar',
            'order': 1
        }))

        assert_that(post_json['modules'][1], has_entries({
            'slug': 'foo',
            'order': 2
        }))

    @patch("performanceplatform.client.admin.AdminAPI.update_dashboard")
    @patch("application.forms.DashboardCreationForm.validate")
    @signed_in(permissions=['signin', 'admin'])
    def test_reorder_modules_on_update_applies_changes_when_form_is_valid(
            self,
            mock_validate,
            mock_update_dashboard,
            mock_list_organisations,
            mock_list_data_sets,
            mock_list_module_types,
            client):
        form_data = {
            'slug': 'valid-slug',
            'modules-0-module_type': '',
            'modules-0-slug': 'foo',
            'modules-1-module_type': '',
            'modules-1-slug': 'bar',

            'modules_order': '2,1',
        }
        mock_validate.return_value = True
        client.post('/admin/dashboards/some_uuid',
                    data=form_data)

        assert_that(len(mock_update_dashboard.call_args_list), equal_to(1))

        uuid = mock_update_dashboard.call_args[0][0]
        assert_that(uuid, equal_to('some_uuid'))

        post_json = mock_update_dashboard.call_args[0][1]

        assert_that(post_json['modules'][0], has_entries({
            'slug': 'bar',
            'order': 1
        }))

        assert_that(post_json['modules'][1], has_entries({
            'slug': 'foo',
            'order': 2
        }))
