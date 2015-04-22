from freezegun import freeze_time
from StringIO import StringIO
from hamcrest import (
    assert_that,
    equal_to,
    ends_with,
    contains_string,
    match_equality,
    has_entries,
    has_item,
    not_none,
)
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

    GET_DATA_SET_RETURN_VALUE = {
        'name': 'apply_uk_visa_transactions_by_channel',
        'data_type': 'transactions-by-channel',
        'data_group': 'apply-uk-visa',
        'bearer_token': 'abc123',
        'upload_format': 'csv',
        'max_age_expected': 1300000
    }

    LIST_MODULE_TYPES_RETURN_VALUE = [
        {
            "id": "3e06c1d4-1bac-4a23-80c6-ac071574fce8",
            "name": "realtime"
        },
        {
            "id": "36546562-b2bd-44a9-b94a-e3cfc472ddf4",
            "name": "single_timeseries"
        },
        {
            "id": "12323445-b2bd-44a9-b94a-e3cfc472ddf4",
            "name": "completion_rate"
        }
    ]

    CREATE_DATA_SET_RETURN_VALUE = {
        'name': 'apply_uk_visa_transactions_by_channel',
        'data_type': 'transactions-by-channel',
        'data_group': 'apply-uk-visa',
        'bearer_token': 'abc123',
        'upload_format': 'csv',
        'max_age_expected': 1300000
    }

    GET_DASHBOARD_RETURN_VALUE = {
        'organisation': {'name': 'Cabinet Office'},
        'slug': 'apply-uk-visa'
    }

    @staticmethod
    def params(options={}):
        params = {
            'digital': 'y',
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

    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('application.controllers.digital_take_up.create_dataset_and_module')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set_transform')
    def test_stores_chosen_channel_options_in_the_session(
            self,
            transform_mock,
            data_set_module_mock,
            get_dashboard_mock
    ):

        data_set_module_mock.return_value = {}, {}, {}

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())
        self.assert_session_contains(
            'channel_choices', ['digital', 'telephone_human'])

    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('application.controllers.digital_take_up.create_dataset_and_module')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set_transform')
    def test_redirects_to_download_template_page(self,
                                                 transform_mock,
                                                 data_set_module_mock,
                                                 get_dashboard_mock):

        data_set_module_mock.return_value = {}, {}, {}

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = self.client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/upload'))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set_transform')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_new_data_set_added_to_existing_module(
            self,
            add_module_patch,
            list_module_types_patch,
            transform_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_data_group_patch,
            get_dashboard_patch,
            client):

        get_data_group_patch.return_value = {'name': 'apply-uk-visa'}

        get_data_set_patch.return_value = None

        create_data_set_patch.return_value = self.CREATE_DATA_SET_RETURN_VALUE

        list_module_types_patch.return_value = \
            self.LIST_MODULE_TYPES_RETURN_VALUE

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())

        add_module_patch.assert_called_with(
            'apply-uk-visa', match_equality(has_entries(
                {
                    "data_group": "apply-uk-visa",
                    "data_type": "digital-takeup",
                    "type_id": "36546562-b2bd-44a9-b94a-e3cfc472ddf4"
                })))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('application.controllers.digital_take_up.create_dataset_and_module')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set_transform')
    def test_set_owning_organisation_in_info(
        self,
        transform_mock,
        dataset_module_mock,
        get_dashboard_mock,
        client
    ):
        organisation = 'BIS'
        get_dashboard_mock.return_value = {
            'organisation': {'name': organisation},
            'slug': 'apply-uk-visa'
        }

        dataset_module_mock.return_value = {}, {}, {}

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())

        # match_equality(not_none()) is used because we dont care what any
        # arguments are except for the 7th argument
        dataset_module_mock.assert_called_with(
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(has_entries(
                {'info': has_item(contains_string(organisation))}
            )),
            match_equality(not_none())
        )

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('application.controllers.digital_take_up.create_dataset_and_module')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set_transform')
    def test_sets_info_to_unknown_when_no_organisation(
            self,
            transform_mock,
            dataset_module_mock,
            get_dashboard_mock,
            client
    ):

        get_dashboard_mock.return_value = {
            'organisation': None,
            'slug': 'apply-uk-visa'
        }

        dataset_module_mock.return_value = {}, {}, {}

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())

        # match_equality(not_none()) is used because we dont care what any
        # arguments are except for the 3rd argument
        dataset_module_mock.assert_called_with(
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(not_none()),
            match_equality(has_entries(
                {'info': has_item(contains_string('Unknown'))}
            )),
            match_equality(not_none()),
        )

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set_transform')
    def test_create_digital_take_up_module_in_stagecraft(
            self,
            transform_patch,
            add_module_patch,
            list_module_types_patch,
            create_data_set_patch,
            get_data_set_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_dashboard_patch,
            client
    ):

        get_dashboard_patch.return_value = {'slug': 'apply-uk-visa'}

        get_data_group_patch.return_value = None

        create_data_group_patch.return_value = {'name': 'apply-uk-visa'}

        get_data_set_patch.return_value = None

        create_data_set_patch.return_value = self.CREATE_DATA_SET_RETURN_VALUE

        list_module_types_patch.return_value = \
            self.LIST_MODULE_TYPES_RETURN_VALUE

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())

        create_data_group_patch.assert_called_with(
            create_data_group_patch.return_value)

        create_data_set_patch.assert_called_with(match_equality(has_entries(
            {
                'data_type': 'digital-takeup',
                'data_group': 'apply-uk-visa',
                'upload_format': 'csv',
                'max_age_expected': 1300000
            }
        )))

        add_module_patch.assert_called_with(
            'apply-uk-visa', match_equality(has_entries(
                {
                    "data_group": "apply-uk-visa",
                    "data_type": "digital-takeup",
                    "type_id": "36546562-b2bd-44a9-b94a-e3cfc472ddf4"
                })))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('application.controllers.digital_take_up.get_or_create_data_group')
    @patch('application.controllers.digital_take_up.'
           'get_or_create_data_set')
    @patch('application.controllers.digital_take_up.create_module_if_not_exists')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set_transforms')
    @patch('performanceplatform.client.admin.AdminAPI.create_transform')
    def test_transform_created(
            self,
            create_transform_patch,
            get_transform_patch,
            create_module_patch,
            data_set_patch,
            data_group_patch,
            get_dashboard_mock,
            client
    ):
        get_dashboard_mock.return_value = self.GET_DASHBOARD_RETURN_VALUE

        get_transform_patch.return_value = []

        create_module_patch.return_value = \
            {'name': 'apply-uk-visa'}, \
            {'name': 'apply_uk_visa_transactions_by_channel'}, \
            {}

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())

        create_transform_patch.assert_called_with(
            {
                "type_id": "8e8d973b-3937-430d-944f-56bbeee13af2",
                "input": {
                    "data-type": "transactions-by-channel",
                    "data-group": "apply-uk-visa"
                },
                "query-parameters": {
                    "collect": ["count:sum"],
                    "group_by": "channel",
                    "period": "week"
                },
                "options": {
                    "denominatorMatcher": ".+",
                    "numeratorMatcher": "^digital$",
                    "matchingAttribute": "channel",
                    "valueAttribute": "count:sum"
                },
                "output": {
                    "data-type": "digital-takeup",
                    "data-group": "apply-uk-visa"
                }
            }
        )

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('application.controllers.digital_take_up.create_dataset_and_module')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set_transforms')
    @patch('performanceplatform.client.admin.AdminAPI.create_transform')
    def test_only_one_transform_created(
            self,
            create_transform_patch,
            get_transform_patch,
            dataset_module_mock,
            get_dashboard_mock,
            client
    ):
        get_dashboard_mock.return_value = self.GET_DASHBOARD_RETURN_VALUE

        get_transform_patch.return_value = {
            "id": "abc1234",
            "query-parameters": {
                "collect": [
                    "count:sum"
                ],
                "group_by": [
                    "channel"
                ],
                "period": "week"
            },
            "output": {
                "data-group": "apply-uk-visa",
                "data-type": "digital-takeup"
            },
            "input": {
                "data-group": "apply-uk-visa",
                "data-type": "transactions-by-channel"
            },
            "type": {
                "function": "backdrop.transformers.tasks.rate.compute",
                "id": "8e8d973b-3937-430d-944f-56bbeee13af2"
            },
            "options": {
                "denominatorMatcher": ".+",
                "numeratorMatcher": "(digital)",
                "matchingAttribute": "channel",
                "valueAttribute": "count:sum"
            }
        }

        dataset_module_mock.return_value = \
            {'name': 'apply-uk-visa'}, \
            {'name': 'apply_uk_visa_transactions_by_channel'}, \
            {}

        with self.client.session_transaction() as session:
            session['upload_choice'] = 'week'

        response = client.post(
            '/dashboard/dashboard-uuid/digital-take-up/channel-options',
            data=self.params())

        assert not create_transform_patch.called


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
            '/dashboard/dashboard-uuid/digital-take-up/upload')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/upload')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_download_slug_renders_download_template_page(self):
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/upload')
        assert_that(response.status, equal_to('200 OK'))

    def test_download_page_contains_a_download_link(self):
        response = self.client.get(
            '/dashboard/dashboard-uuid/digital-take-up/upload')
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

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        dash_id = '77f1351a-e62f-47fe-bc09-fc69723573be'
        self.app = app.test_client()
        self.upload_url = \
            '/dashboard/{}/digital-take-up/upload'.format(dash_id)
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
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    def test_handles_invalid_spreadsheet(
            self,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_dashboard_patch.return_value = {'slug': 'apply-uk-visa'}

        get_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }

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

    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    def test_data_added_to_backdrop(self, get_data_set_patch):
        pass
