from application import app

from freezegun import freeze_time

from hamcrest import (
    assert_that,
    contains_string,
    equal_to
)

from mock import patch

from tests.application.support.flask_app_test_case import FlaskAppTestCase


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

    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    def test_data_added_to_backdrop(self, get_data_set_patch):
        pass
