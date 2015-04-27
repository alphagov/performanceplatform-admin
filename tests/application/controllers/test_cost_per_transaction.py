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
    def test_serves_quarterly_dates(
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
