from StringIO import StringIO
from application import app

from freezegun import freeze_time

from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    ends_with
)

from mock import patch, Mock

from tests.application.support.flask_app_test_case import(
    FlaskAppTestCase,
    signed_in)

from requests import HTTPError, Response


class DownloadPageTestCase(FlaskAppTestCase):

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
            '/dashboard/dashboard-uuid/cost-per-transaction/upload')
        assert_that(response.status, equal_to('302 FOUND'))

    def test_authorised_user_is_required(self):
        with self.client.session_transaction() as session:
            session['oauth_user'] = {'permissions': ['signin']}
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/upload')
        assert_that(response.status, equal_to('302 FOUND'))

    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard',
           return_value={})
    def test_render_download_template_page(
            self, mock_get_dashboard):
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/upload')
        assert_that(response.status, equal_to('200 OK'))

    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard',
           return_value={})
    def test_download_page_contains_a_download_link(
            self, mock_get_dashboard):
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/upload')
        url = '/dashboard-uuid/cost-per-transaction/spreadsheet-template'
        assert_that(response.data, contains_string(url))

    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard',
           return_value={})
    def test_render_download_template_page_contains_any_errors(
            self, mock_get_dashboard):
        with self.client.session_transaction() as session:
            session['upload_data'] = {
                'payload': ['Message 1', 'Message 2']
            }
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/upload')
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Message 1'))
        assert_that(response.data, contains_string('Message 2'))

    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard',
           return_value={})
    def test_csv_file_download(
            self, mock_get_dashboard):
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/'
            'spreadsheet-template')
        assert_that(response.headers[2][1], contains_string('attachment'))
        assert_that(response.headers[2][1],
                    contains_string('filename=cost_per_transaction.csv'))

    @freeze_time("2015-03-26")
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard',
           return_value={})
    def test_serves_quarterly_dates_full_year(
            self, mock_get_dashboard):
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/'
            'spreadsheet-template')
        expected_content = (
            "_timestamp,end_at,period,channel,count,comment\n"
            "2014-01-01T00:00:00,2014-03-31T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
            "2014-04-01T00:00:00,2014-06-30T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
            "2014-07-01T00:00:00,2014-09-30T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
            "2014-10-01T00:00:00,2014-12-31T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
        )
        assert_that(response.data, equal_to(expected_content))

    @freeze_time("2015-04-26")
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard',
           return_value={})
    def test_serves_quarterly_dates_cross_year(
            self, mock_get_dashboard):
        response = self.client.get(
            '/dashboard/dashboard-uuid/cost-per-transaction/'
            'spreadsheet-template')
        expected_content = (
            "_timestamp,end_at,period,channel,count,comment\n"
            "2014-04-01T00:00:00,2014-06-30T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
            "2014-07-01T00:00:00,2014-09-30T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
            "2014-10-01T00:00:00,2014-12-31T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
            "2015-01-01T00:00:00,2015-03-31T00:00:00,quarterly,cost_per_transaction_digital,0,\n"  # noqa
        )
        assert_that(response.data, equal_to(expected_content))


class UploadPageTestCase(FlaskAppTestCase):

    def setUp(self):
        app.config['WTF_CSRF_ENABLED'] = False
        self.dash_id = '77f1351a-e62f-47fe-bc09-fc69723573be'
        self.app = app.test_client()
        self.upload_url = \
            '/dashboard/{}/cost-per-transaction/upload'.format(self.dash_id)
        self.file_data = {
            'file': (StringIO('Week ending,API,Paper form\n2014-08-05,40,10'),
                     'test_upload.csv')}

        self.upload_spreadsheet_patcher = patch(
            'application.controllers.upload.upload_spreadsheet')
        self.upload_spreadsheet_mock = self.upload_spreadsheet_patcher.start()
        self.upload_spreadsheet_mock.return_value = ([], False)

        self.generate_bearer_token_patcher = patch(
            "application.controllers.builder"
            ".cost_per_transaction.generate_bearer_token")
        self.generate_bearer_token_mock = \
            self.generate_bearer_token_patcher.start()
        self.generate_bearer_token_mock.return_value = "abc123def"

    def tearDown(self):
        patch.stopall()

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_handles_no_spreadsheet(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        self.upload_spreadsheet_patcher.stop()

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        get_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }
        get_data_group_patch.return_value = {
            'name': 'visas'
        }
        add_module_to_dashboard_patch.return_value = {}

        self.file_data = {
            'file': (StringIO('Week ending,API,Paper form\n2014-08-05,40,10'),
                     '')}

        response = client.post(self.upload_url, data=self.file_data)

        # see line 117 of application/controllers/upload.py
        # to see why this is expected.
        assert_that(
            self.get_from_session('upload_data')['payload'],
            equal_to(['Please choose a file to upload']))
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(
            response.headers['Location'],
            ends_with("/dashboard/{}"
                      "/cost-per-transaction/upload".format(
                          self.dash_id)))
        with client.session_transaction() as session:
            assert_that(
                '_flashes' in session,
                equal_to(False))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_handles_invalid_spreadsheet(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        get_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }
        get_data_group_patch.return_value = {
            'name': 'visas'
        }
        add_module_to_dashboard_patch.return_value = {}

        self.upload_spreadsheet_mock.return_value = \
            (['Message 1', 'Message 2'], False)

        response = client.post(self.upload_url, data=self.file_data)

        # see line 117 of application/controllers/upload.py
        # to see why this is expected.
        assert_that(
            self.get_from_session('upload_data')['payload'],
            equal_to(['Message 1', 'Message 2']))
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(
            response.headers['Location'],
            ends_with("/dashboard/{}"
                      "/cost-per-transaction/upload".format(
                          self.dash_id)))
        with client.session_transaction() as session:
            assert_that(
                '_flashes' in session,
                equal_to(False))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_spreadsheet_valid(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        get_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }
        get_data_group_patch.return_value = {
            'name': 'visas'
        }
        add_module_to_dashboard_patch.return_value = {}

        response = client.post(self.upload_url, data=self.file_data)

        # see line 117 of application/controllers/upload.py
        # to see why this is expected.
        assert_that(
            self.get_from_session('upload_data')['payload'],
            equal_to([]))
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(
            response.headers['Location'],
            ends_with("/dashboard/{}"
                      "/cost-per-transaction/upload/success".format(
                          self.dash_id)))

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_nothing_created_if_data_set_and_group_exist(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        get_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }
        get_data_group_patch.return_value = {
            'name': 'visas'
        }
        add_module_to_dashboard_patch.return_value = {}

        client.post(self.upload_url, data=self.file_data)

        get_data_set_patch.assert_called_once_with(
            "visas", "cost-per-transaction")
        assert_that(create_data_set_patch.called, equal_to(False))
        get_data_group_patch.assert_called_once_with("visas")
        assert_that(create_data_group_patch.called, equal_to(False))
        list_module_types_patch.assert_called_once_with()
        add_module_to_dashboard_patch.assert_called_once_with('visas', {
            'data_group': 'visas',
            'data_type': 'cost-per-transaction',
            'title': 'Cost per transaction'})

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_create_data_group_and_set_if_nothing_exists(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

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
        get_data_group_patch.return_value = None
        create_data_group_patch.return_value = {
            'name': 'visas'
        }
        add_module_to_dashboard_patch.return_value = {}

        client.post(self.upload_url, data=self.file_data)

        get_data_set_patch.assert_called_once_with(
            "visas", "cost-per-transaction")
        create_data_set_patch.assert_called_once_with({
            'upload_format': 'csv',
            'bearer_token': 'abc123def',
            'data_group': 'visas',
            'data_type': 'cost-per-transaction',
            'max_age_expected': 0})
        get_data_group_patch.assert_called_once_with("visas")
        create_data_group_patch.assert_called_once_with({'name': 'visas'})
        list_module_types_patch.assert_called_once_with()
        add_module_to_dashboard_patch.assert_called_once_with('visas', {
            'data_group': 'visas',
            'data_type': 'cost-per-transaction',
            'title': 'Cost per transaction'})

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_if_HTTPError_on_get_data_set(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        # ===
        response_json_mock = Mock()
        response_json_mock.return_value = {'message': 'Error message'}
        response = Response()
        response.status_code = 400
        response.json = response_json_mock
        error = HTTPError('Error message', response=response)
        # ===
        get_data_set_patch.side_effect = error

        response = client.post(self.upload_url, data=self.file_data)

        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(
            response.headers['Location'],
            ends_with("/dashboard/{}"
                      "/cost-per-transaction/upload".format(
                          self.dash_id)))

        with client.session_transaction() as session:
            flash_status = session['_flashes'][0][0]
            assert_that(
                flash_status,
                equal_to('error'),
                "There was a problem setting up the module, please "
                "contact the Performance Platform if the problem persists.")
            # reset flashes
            session['_flashes'] = []

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_if_HTTPError_on_get_data_group(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        # ===
        response_json_mock = Mock()
        response_json_mock.return_value = {'message': 'Error message'}
        response = Response()
        response.status_code = 400
        response.json = response_json_mock
        error = HTTPError('Error message', response=response)
        # ===
        get_data_group_patch.side_effect = error

        response = client.post(self.upload_url, data=self.file_data)

        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(
            response.headers['Location'],
            ends_with("/dashboard/{}"
                      "/cost-per-transaction/upload".format(
                          self.dash_id)))

        with client.session_transaction() as session:
            flash_status = session['_flashes'][0][0]
            assert_that(
                flash_status,
                equal_to('error'),
                "There was a problem setting up the module, please "
                "contact the Performance Platform if the problem persists.")
            # reset flashes
            session['_flashes'] = []

    @signed_in(permissions=['signin', 'dashboard'])
    @patch('performanceplatform.client.admin.AdminAPI.get_dashboard')
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_set')
    @patch("application.controllers.builder"
           ".cost_per_transaction.get_module_config_for_cost_per_transaction")
    @patch('performanceplatform.client.admin.AdminAPI.get_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.create_data_group')
    @patch('performanceplatform.client.admin.AdminAPI.list_module_types')
    @patch('performanceplatform.client.admin.AdminAPI.add_module_to_dashboard')
    def test_continues_if_add_module_fails(
            self,
            add_module_to_dashboard_patch,
            list_module_types_patch,
            create_data_group_patch,
            get_data_group_patch,
            get_module_config_patch,
            create_data_set_patch,
            get_data_set_patch,
            get_dashboard_patch,
            client):

        get_module_config_patch.return_value = {
            'title': 'Cost per transaction'}

        get_dashboard_patch.return_value = {
            'slug': 'visas'}

        get_data_set_patch.return_value = {
            'name': 'apply_uk_visa_transactions_by_channel',
            'data_type': 'transactions-by-channel',
            'data_group': 'apply-uk-visa',
            'bearer_token': 'abc123',
            'upload_format': 'csv',
            'auto_ids': '_timestamp, period, channel',
            'max_age_expected': 1300000
        }
        get_data_group_patch.return_value = {
            'name': 'visas'
        }
        # ===
        response = Mock()
        response.status_code = 400
        response.text = 'Module with this Dashboard and Slug already exists'
        error = HTTPError('Error message', response=response)
        # ===
        add_module_to_dashboard_patch.side_effect = error

        response = client.post(self.upload_url, data=self.file_data)

        # see line 117 of application/controllers/upload.py
        # to see why this is expected.
        assert_that(
            self.get_from_session('upload_data')['payload'],
            equal_to([]))
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(
            response.headers['Location'],
            ends_with("/dashboard/{}"
                      "/cost-per-transaction/upload/success".format(
                          self.dash_id)))

        get_data_set_patch.assert_called_once_with(
            "visas", "cost-per-transaction")
        assert_that(create_data_set_patch.called, equal_to(False))
        get_data_group_patch.assert_called_once_with("visas")
        assert_that(create_data_group_patch.called, equal_to(False))
        list_module_types_patch.assert_called_once_with()
        add_module_to_dashboard_patch.assert_called_once_with('visas', {
            'data_group': 'visas',
            'data_type': 'cost-per-transaction',
            'title': 'Cost per transaction'})
