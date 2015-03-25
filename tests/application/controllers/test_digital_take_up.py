from tests.application.support.flask_app_test_case import FlaskAppTestCase
from application import app
from freezegun import freeze_time
from hamcrest import (
    assert_that,
    equal_to,
    contains_string,
    ends_with
)


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
