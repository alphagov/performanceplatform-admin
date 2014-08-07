from hamcrest import assert_that, equal_to, ends_with, contains_string
from mock import patch, Mock
from StringIO import StringIO
from tests.admin.support.flask_app_test_case import FlaskAppTestCase
import requests


class UploadTestCase(FlaskAppTestCase):

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_user_can_post_to_upload_data(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_admin_client_patch,
            signed_in_patch):
        is_virus_patch.return_value = False
        signed_in_patch.return_value = True
        client_mock = Mock()
        client_mock.get_data_set.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }
        get_admin_client_patch.return_value = client_mock

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

        upload_done_path = '/upload-data'
        assert_that(response.headers['Location'], ends_with(upload_done_path))
        assert_that(response.status_code, equal_to(302))

    # this could be rolled into the previous test
    # if we can get inspecting flash and session working
    # instead of checking rendered content
    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_display_okay_if_success(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_admin_client_patch,
            signed_in_patch):
        is_virus_patch.return_value = False
        signed_in_patch.return_value = True
        client_mock = Mock()
        client_mock.get_data_set.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }
        client_mock.list_data_sets.return_value = [{}]
        get_admin_client_patch.return_value = client_mock

        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        with self.client as client:
            with client.session_transaction() as sess:
                sess.update({
                    'oauth_token': {
                        'access_token': 'token'},
                    'oauth_user': 'a user'})
            response = client.post(
                '/upload-data/carers-allowance/volumetrics',
                data=post_data, follow_redirects=True)

            assert_that(
                response.data,
                contains_string(
                    'carers-allowance volumetrics'))
            assert_that(
                response.data,
                contains_string(
                    'Your data uploaded successfully into the dataset'))

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_ask_for_file_if_none_chosen(
            self,
            data_set_post_patch,
            get_admin_client_patch,
            signed_in_patch):
        signed_in_patch.return_value = True
        client_mock = Mock()
        client_mock.get_data_set.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }
        get_admin_client_patch.return_value = client_mock

        post_data = {
            'carers-allowance-volumetrics-file': (None, "")
        }
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data, follow_redirects=True)

        assert_that(
            response.data,
            contains_string(
                'Please choose a file to upload'))

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    @patch('admin.files.uploaded.UploadedFile.validate')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_problem_in_spreadsheet_prevents_post_to_backdrop(
            self,
            data_set_post_patch,
            validate_patch,
            get_admin_client_patch,
            signed_in_patch):
        validate_patch.return_value = ["99"]
        client_mock = Mock()
        client_mock.get_data_set.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }
        get_admin_client_patch.return_value = client_mock

        signed_in_patch.return_value = True
        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data)
        assert_that(data_set_post_patch.called, equal_to(False))

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    def test_no_data_set_config_returns_error(
            self,
            get_admin_client_patch,
            signed_in_patch):
        signed_in_patch.return_value = True
        client_mock = Mock()
        client_mock.get_data_set.return_value = None
        get_admin_client_patch.return_value = client_mock
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data={'file': (StringIO('data'), 'file.xlsx')})

        assert_that(response.data, contains_string(
            'There is no data set of for data-group'))
        assert_that(response.status_code, equal_to(404))

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    def test_http_error_from_stagecraft_flashes_message(
            self,
            get_admin_client_patch,
            signed_in_patch):
        signed_in_patch.return_value = True
        bad_response = requests.Response()
        bad_response.status_code = 403
        bad_response.json = Mock(return_value={})
        http_error = requests.HTTPError()
        http_error.response = bad_response
        client_mock = Mock()
        client_mock.get_data_set.side_effect = http_error
        get_admin_client_patch.return_value = client_mock
        response = self.client.post(
            '/upload-data/carers-allowance/volumetrics',
            data={'file': (StringIO('data'), 'file.xlsx')})

        self.assert_flashes(
            'Stagecraft returned status code <403> with json: {}')

        assert_that(response.headers['Location'], ends_with('/upload-data'))
        assert_that(response.status_code, equal_to(302))

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_http_error_from_backdrop_flashes_message(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_admin_client_patch,
            signed_in_patch):
        is_virus_patch.return_value = False
        client_mock = Mock()
        client_mock.get_data_set.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }
        get_admin_client_patch.return_value = client_mock

        signed_in_patch.return_value = True
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
            data=post_data)

        self.assert_flashes(
            'Backdrop returned status code <401> with json: {}')
        assert_that(response.headers['Location'], ends_with('/upload-data'))
        assert_that(response.status_code, equal_to(302))

    @patch('admin.helpers.signed_in')
    @patch('admin.helpers.get_admin_client')
    @patch('admin.files.uploaded.UploadedFile.validate')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_redirect_to_error_if_problems(
            self,
            data_set_post_patch,
            validate_patch,
            get_admin_client_patch,
            signed_in_patch):
        validate_patch.return_value = ["99"]
        client_mock = Mock()
        client_mock.get_data_set.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }
        get_admin_client_patch.return_value = client_mock

        signed_in_patch.return_value = True
        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        with self.client as client:
            with client.session_transaction() as sess:
                sess.update({
                    'oauth_token': {
                        'access_token': 'token'},
                    'oauth_user': 'a user'})
            response = client.post(
                '/upload-data/carers-allowance/volumetrics',
                data=post_data, follow_redirects=True)

            assert_that(
                response.data,
                contains_string(
                    'We tried to upload your data into the dataset'))
            assert_that(
                response.data,
                contains_string(
                    'carers-allowance volumetrics'))
            # doesn't work with follow redirects
            # assert_that(response.headers['Location'], ends_with('/error'))
            # assert_that(response.status_code, equal_to(302))

    @patch('performanceplatform.client.admin.AdminAPI.list_data_sets')
    def test_data_sets_redirects_to_sign_out_when_403_on_data_set_list(
            self,
            mock_data_set_list):
        bad_response = requests.Response()
        bad_response.status_code = 403
        http_error = requests.exceptions.HTTPError()
        http_error.response = bad_response
        mock_data_set_list.side_effect = http_error
        with self.client as client:
            with client.session_transaction() as sess:
                sess.update({
                    'oauth_token': {
                        'access_token': 'token'},
                    'oauth_user': 'a user'})
            response = client.get("/upload-data")
            assert_that(response.status_code, equal_to(302))
            assert_that(
                response.headers['Location'],
                ends_with('/sign-out'))
