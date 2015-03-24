from freezegun import freeze_time
from StringIO import StringIO
from hamcrest import assert_that, equal_to, ends_with, contains_string
from application import app
from tests.application.support.flask_app_test_case import (
    FlaskAppTestCase, signed_in)
from mock import patch


class UploadOptionsPageTestCase(FlaskAppTestCase):

    @staticmethod
    def params(options={}):
        params = {
            'upload_option': 'week'
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
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_upload_options_slug_renders_upload_options_page(self):
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options')
        assert_that(response.status, equal_to('200 OK'))

    def test_upload_option_field_is_required(self):
        data = self.params({'upload_option': ''})
        response = self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options',
            data=data)
        assert_that(response.data, contains_string(
            'select an upload option'))

    def test_stores_chosen_option_in_the_session(self):
        self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options',
            data=self.params())
        self.assert_session_contains('upload_choice', 'week')

    def test_redirects_to_channel_options_page(self):
        response = self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options',
            data=self.params())
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/channel-options'))

    def test_api_choice_redirects_to_api_get_in_touch_page(self):
        data = self.params({'upload_option': 'api'})
        response = self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/upload-options',
            data=data)
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/api-get-in-touch'))


class ChannelOptionsPageTestCase(FlaskAppTestCase):

    @staticmethod
    def params(options={}):
        params = {
            'website': 'y',
            'telephone_human': 'y'
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
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_channel_options_slug_renders_channel_choices_page(self):
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options')
        assert_that(response.status, equal_to('200 OK'))

    def test_one_or_more_channel_options_are_required(self):
        response = self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data={})
        assert_that(response.data, contains_string(
            'select one or more channel options'))

    def test_stores_chosen_channel_options_in_the_session(self):
        self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())
        self.assert_session_contains(
            'channel_choices', ['website', 'telephone_human'])

    def test_redirects_to_download_template_page(self):
        response = self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/download'))


class DownloadTemplatePageTestCase(FlaskAppTestCase):

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
            '/dashboard/dashboard-uuid/digital-take-up/download')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/download')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_download_slug_renders_download_template_page(self):
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/download')
        assert_that(response.status, equal_to('200 OK'))

    def test_download_page_contains_a_download_link(self):
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/download')
        url = '/dashboard-uuid/digital-take-up/spreadsheet-template'
        assert_that(response.data, contains_string(url))

    def test_spreadsheet_template_slug_responds_with_a_csv_file(self):
        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'
            session['channel_choices'] = ['api', 'face_to_face']
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/spreadsheet-template')
        assert_that(response.headers[2][1], contains_string('attachment'))
        assert_that(response.headers[2][1],
                    contains_string('filename=digital_take_up.csv'))

    @freeze_time("2015-03-26")
    def test_serves_a_weekly_csv_file_for_chosen_channels(self):
        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'
            session['channel_choices'] = ['api', 'face_to_face']
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/spreadsheet-template')
        expected_content = (
            "_timestamp,period,channel,count\n"
            "2015-03-16T00:00:00+00:00,week,api,0\n"
            "2015-03-16T00:00:00+00:00,week,face_to_face,0\n"
        )
        assert_that(response.data, equal_to(expected_content))

    @freeze_time("2015-03-26")
    def test_serves_a_monthly_csv_file_for_chosen_channels(self):
        with self.client.session_transaction() as session:
            session['upload_choice'] = 'month'
            session['channel_choices'] = ['api', 'face_to_face']
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/spreadsheet-template')
        expected_content = (
            "_timestamp,period,channel,count\n"
            "2015-02-01T00:00:00+00:00,month,api,0\n"
            "2015-02-01T00:00:00+00:00,month,face_to_face,0\n"
        )
        assert_that(response.data, equal_to(expected_content))


class UploadPageTestCase(FlaskAppTestCase):

    GET_DATA_SET_RETURN_VALUE = {
        'name': 'apply_uk_visa_transactions_by_channel',
        'data_type': 'transactions-by-channel',
        'data_group': 'apply-uk-visa',
        'bearer_token': 'abc123',
        'upload_format': 'csv',
        'auto_ids': '_timestamp, period, channel',
        'max_age_expected': 1300000
    }

    LIST_MODULES_RETURN_VALUE = [
        {
            "data_type": "transactions-by-channel",
            "id": "a1234-b5-67g",
            "data_group": "prison-visits",
            "title": "Digital take-up",
            "slug": "digital-takeup",
            "dashboard": {
                    "id": "a1234-b5-67d"
            },
            "type": {
                "id": "d1234-b5-67e"
            },
            "description": "Online transactions",
            "info": ["Data source: Department for Work and Pensions",
                     "<a href='/service-manual/measurement/digital-takeup' rel='external'>Digital take-up</a> measures the percentage of completed applications that are made through a digital channel versus non-digital channels."],

        }
    ]

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.upload_url = \
            '/dashboard/apply-uk-visa/digital-take-up/upload'
        self.file_data = {
            'file': (StringIO('Week ending,API,Paper form\n2014-08-05,40,10'),
                     'test_upload.csv')}

        self.upload_spreadsheet_patcher = patch(
            'application.controllers.upload.upload_spreadsheet')
        self.upload_spreadsheet_mock = self.upload_spreadsheet_patcher.start()
        self.upload_spreadsheet_mock.return_value = ([], False)

    def tearDown(self):
        self.upload_spreadsheet_patcher.stop()

    @signed_in(permissions=['signin', 'dashboard'])
    def test_upload_slug_renders_digital_take_up_upload_page(self, client):
        response = client.get(self.upload_url)
        assert_that(response.status, equal_to('200 OK'))

    def test_authenticated_user_is_required(self):
        response = self.app.get(self.upload_url)
        assert_that(response.status, equal_to('302 FOUND'))

    @signed_in()
    def test_user_with_dashboard_permission_is_required(self, client):
        response = client.get(self.upload_url)
        assert_that(response.status, equal_to('302 FOUND'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch(
        'performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard')
    def test_get_list_of_modules_for_dashboard(
            self, list_modules_patch,
            create_data_set_patch,
            get_data_set_patch, client):
        get_data_set_patch.return_value = self.GET_DATA_SET_RETURN_VALUE

        response = client.post(self.upload_url, data=self.file_data)

        assert list_modules_patch.called

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch(
        'performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_create_digital_take_up_module_in_stagecraft(
            self, add_module_patch, list_module_types_patch,
            list_modules_patch, create_data_set_patch,
            get_data_set_patch, client):

        get_data_set_patch.return_value = None

        create_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }

        list_modules_patch.return_value = \
            [
                {
                    "data_type": "user-satisfaction-score",
                    "id": "a1234-b5-67c",
                    "data_group": "prison-visits",
                    "title": "User satisfaction",
                    "slug": "user-satisfaction",
                    "dashboard": {
                        "id": "b1234-b5-67c"
                    },
                    "type": {
                        "id": "c1234-b5-67c"
                    }
                },
                {
                    "data_type": "completion-rate",
                    "id": "a1234-b5-67f",
                    "data_group": "prison-visits",
                    "title": "Completion rate",
                    "slug": "completion-rate",
                    "dashboard": {
                        "id": "a1234-b5-67d"
                    },
                    "type": {
                        "id": "a1234-b5-67e"
                    }
                }
            ]

        list_module_types_patch.return_value = [
            {
                "id": "3e06c1d4-1bac-4a23-80c6-ac071574fce8",
                "name": "realtime"
            },
            {
                "id": "36546562-b2bd-44a9-b94a-e3cfc472ddf4",
                "name": "single_timeseries"
            }
        ]

        response = client.post(self.upload_url, data=self.file_data)
        assert get_data_set_patch.called

        assert list_module_types_patch.called

        expected_dataset_post_data = {
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }

        create_data_set_patch.assert_called_with(expected_dataset_post_data)

        expected_post_data = {
            "data_set": 'apply_uk_visa_transactions_by_channel',
            "slug": "digital-takeup",
            "type_id": "36546562-b2bd-44a9-b94a-e3cfc472ddf4",
            "title": "Digital take-up",
            "description": "What percentage of transactions were completed using the online service",
            "info": ["Data source: Department for Work and Pensions",
                     "<a href='/service-manual/measurement/digital-takeup' rel='external'>Digital take-up</a> measures the percentage of completed applications that are made through a digital channel versus non-digital channels."],
            "options": {"value-attribute": "transactions_by_channels"},
            "order": 1
        }

        add_module_patch.assert_called_with(
            'apply-uk-visa', expected_post_data)

    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch(
        'performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_module_not_created_when_module_and_data_set_exist(
            self, add_module_patch, list_module_types_patch,
            list_modules_patch, create_data_set_patch,
            get_data_set_patch):
        get_data_set_patch.return_value = self.GET_DATA_SET_RETURN_VALUE

        list_modules_patch.return_value = [
            {
                "data_type": "user-satisfaction-score",
                "id": "a1234-b5-67c",
                "data_group": "prison-visits",
                "title": "User satisfaction",
                "slug": "user-satisfaction",
                "dashboard": {
                    "id": "b1234-b5-67c"
                },
                "type": {
                    "id": "c1234-b5-67c"
                }
            },
            {
                "data_type": "completion-rate",
                "id": "a1234-b5-67f",
                "data_group": "prison-visits",
                "title": "Completion rate",
                "slug": "completion-rate",
                "dashboard": {
                    "id": "a1234-b5-67d"
                },
                "type": {
                    "id": "a1234-b5-67e"
                }
            },
            {
                "data_type": "transactions-by-channel",
                "id": "a1234-b5-67g",
                "data_group": "prison-visits",
                "title": "Digital take up",
                "slug": "digital-takeup",
                "dashboard": {
                    "id": "a1234-b5-67d"
                },
                "type": {
                    "id": "d1234-b5-67e"
                }
            }
        ]

        response = self.app.post(self.upload_url, data=self.file_data)

        assert not create_data_set_patch.called
        assert not add_module_patch.called

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch(
        'performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_new_data_set_added_to_existing_module(
            self, add_module_patch, list_modules_patch, create_data_set_patch,
            get_data_set_patch, client):
        get_data_set_patch.return_value = None
        create_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }

        list_modules_patch.return_value = self.LIST_MODULES_RETURN_VALUE

        response = client.post(self.upload_url, data=self.file_data)

        assert create_data_set_patch.called

        expected_post_data = {
            "id": "a1234-b5-67g",
            "data_set": 'apply_uk_visa_transactions_by_channel',
            "slug": "digital-takeup",
            "type_id": "d1234-b5-67e",
            "title": "Digital take-up",
            "description": "Online transactions",
            "info": ["Data source: Department for Work and Pensions",
                     "<a href='/service-manual/measurement/digital-takeup' rel='external'>Digital take-up</a> measures the percentage of completed applications that are made through a digital channel versus non-digital channels."],
            "options": {"value-attribute": "transactions_by_channels"},
            "order": 1
        }

        add_module_patch.assert_called_with(
            'apply-uk-visa', expected_post_data)

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch(
        'performanceplatform.client.admin.AdminAPI.list_modules_on_dashboard')
    def test_handles_invalid_spreadsheet(
            self, list_modules_patch, get_data_set_patch, client):
        get_data_set_patch.return_value = self.GET_DATA_SET_RETURN_VALUE

        list_modules_patch.return_value = self.LIST_MODULES_RETURN_VALUE

        self.upload_spreadsheet_mock.return_value = \
            (['Message 1', 'Message 2'], False)

        response = client.post(self.upload_url, data=self.file_data)

        assert_that(
            self.get_from_session('upload_data')['payload'],
            equal_to(['Message 1', 'Message 2']))

    def test_create_bearer_token(self):
        # need a bearer token to create a data set
        pass

    def test_set_that_data_is_collected_weekly_in_data_set(self):
        # set max_age_expected to 1300000
        pass

    def test_set_that_data_is_collected_monthly_in_data_set(self):
        # set max_age_expected to 5200000
        pass

    def test_time_period_in_data_matches_time_period_data_set(self):
        # if the data set already exists, check that the time period in the
        # csv file matches.
        pass

    def test_set_owning_organisation_in_info(self):
        pass

    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    def test_data_added_to_backdrop(self, get_data_set_patch):
        pass
