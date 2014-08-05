from hamcrest import assert_that, is_, equal_to, ends_with, contains_string
from mock import patch, Mock
from StringIO import StringIO
from tests.admin.support.flask_app_test_case import FlaskAppTestCase
import requests


class UploadTestCase(FlaskAppTestCase):

    @patch('admin.helpers.get_context')
    @patch('admin.upload.get_data_set_config')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_user_can_post_to_upload_data(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_data_set_config_patch,
            get_context_patch):
        is_virus_patch.return_value = False
        get_context_patch.return_value = {
            'user': {
                'email': 'test@example.com'}}
        get_data_set_config_patch.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }

        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data)

        expected_post = [{u'_timestamp': u'2014-08-05T00:00:00Z', u'foo': 40}]
        data_set_post_patch.assert_called_once_with(expected_post)

        upload_done_path = '/upload-data/carers-allowance/volumetrics/done'
        assert_that(response.headers['Location'], ends_with(upload_done_path))
        assert_that(response.status_code, equal_to(302))

    @patch('admin.helpers.get_context')
    @patch('admin.upload.get_data_set_config')
    def test_no_data_set_config_returns_error(
            self,
            get_data_set_config_patch,
            get_context_patch):
        get_context_patch.return_value = {
            'user': {'email': 'test@example.com'}}
        get_data_set_config_patch.return_value = None
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data={'file': (StringIO('data'), 'file.xlsx')})

        # self.assert_flashes('Post added')
        assert_that(response.data, contains_string(
            'There is no data set of for data-group'))
        assert_that(response.status_code, equal_to(404))

    @patch('admin.helpers.get_context')
    @patch('admin.upload.get_data_set_config')
    def test_http_error_from_stagecraft_flashes_message(
            self,
            get_data_set_config_patch,
            get_context_patch):
        get_context_patch.return_value = {
            'user':
                {'email': 'test@example.com'},
            'environment': {}}
        bad_response = requests.Response()
        bad_response.status_code = 403
        bad_response.json = Mock(return_value={})
        http_error = requests.HTTPError()
        http_error.response = bad_response
        get_data_set_config_patch.side_effect = http_error
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data={'file': (StringIO('data'), 'file.xlsx')},
            follow_redirects=True)

        assert_that(
            response.data,
            contains_string(
                'Stagecraft returned status code &lt;403&gt; with json: {}'))

    @patch('admin.helpers.get_context')
    @patch('admin.upload.get_data_set_config')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_http_error_from_backdrop_flashes_message(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_data_set_config_patch,
            get_context_patch):
        is_virus_patch.return_value = False
        get_data_set_config_patch.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }

        get_context_patch.return_value = {
            'user':
                {'email': 'test@example.com'},
            'environment': {}}
        bad_response = requests.Response()
        bad_response.status_code = 401
        bad_response.json = Mock(return_value={})
        http_error = requests.HTTPError()
        http_error.response = bad_response
        data_set_post_patch.side_effect = http_error
        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data, follow_redirects=True)

        assert_that(
            response.data,
            contains_string(
                'Backdrop returned status code &lt;401&gt; with json: {}'))

    def test_validation_error_flashed_message(self):
        pass

    def test_nasty_virus_does_something(self):
        pass

    def test_probem_in_spreadsheet_prevents_post_to_backdrop(self):
        assert_that(1, is_(2))

    def test_no_problems_after_post_flashes_success(self):
        assert_that(1, is_(2))

    def test_problems_after_post_flashes_erorr(self):
        assert_that(1, is_(2))
