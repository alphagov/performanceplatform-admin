from hamcrest import assert_that, equal_to, ends_with, contains_string
from mock import patch, Mock
from StringIO import StringIO
from tests.admin.support.flask_app_test_case import FlaskAppTestCase, signed_in
import requests


class UploadTestCase(FlaskAppTestCase):

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_user_can_post_to_upload_data(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_data_set_patch,
            client):
        is_virus_patch.return_value = False
        get_data_set_patch.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }

        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        response = client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data)

        expected_post = [{u'_timestamp': u'2014-08-05T00:00:00Z', u'foo': 40}]
        data_set_post_patch.assert_called_once_with(expected_post)

        upload_done_path = '/upload-data'
        assert_that(response.headers['Location'], ends_with(upload_done_path))
        assert_that(response.status_code, equal_to(302))

        self.assert_session_contains(
            'upload_okay_message',
            {u'data_type': u'volumetrics', u'data_group': u'carers-allowance'})

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_ask_for_file_if_none_chosen(
            self,
            data_set_post_patch,
            get_data_set_patch,
            client):
        get_data_set_patch.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }

        post_data = {
            'carers-allowance-volumetrics-file': (None, "")
        }
        response = client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data)

        self.assert_flashes('Please choose a file to upload')
        assert_that(response.headers['Location'], ends_with('/upload-data'))
        assert_that(response.status_code, equal_to(302))

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    def test_no_data_set_config_returns_error(
            self,
            get_data_set_patch,
            client):
        get_data_set_patch.return_value = None
        response = client.post(
            '/upload-data/carers-allowance/volumetrics',
            data={'file': (StringIO('data'), 'file.xlsx')})

        assert_that(response.data, contains_string(
            'There is no data set of for data-group'))
        assert_that(response.status_code, equal_to(404))

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    def test_http_error_from_stagecraft_flashes_message(
            self,
            get_data_set_patch,
            client):
        bad_response = requests.Response()
        bad_response.status_code = 403
        bad_response.json = Mock(return_value={})
        http_error = requests.HTTPError()
        http_error.response = bad_response
        get_data_set_patch.side_effect = http_error
        response = client.post(
            '/upload-data/carers-allowance/volumetrics',
            data={'file': (StringIO('data'), 'file.xlsx')})

        self.assert_flashes(
            'Stagecraft returned status code <403> with json: {}')

        assert_that(response.headers['Location'], ends_with('/upload-data'))
        assert_that(response.status_code, equal_to(302))

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_http_error_from_backdrop_flashes_message(
            self,
            data_set_post_patch,
            is_virus_patch,
            get_data_set_patch,
            client):
        is_virus_patch.return_value = False
        get_data_set_patch.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }

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
        response = client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data)

        self.assert_flashes(
            'Backdrop returned status code <401> with json: {}')
        assert_that(response.headers['Location'], ends_with('/upload-data'))
        assert_that(response.status_code, equal_to(302))

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.get_data_set')
    @patch('admin.files.uploaded.UploadedFile.validate')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_redirect_to_error_if_problems_and_prevent_post(
            self,
            data_set_post_patch,
            validate_patch,
            get_data_set_patch,
            client):
        validate_patch.return_value = ["99"]
        get_data_set_patch.return_value = {
            'bearer_token': 'abc123', 'foo': 'bar'
        }

        post_data = {
            'carers-allowance-volumetrics-file':
                (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'),
                    'MYSPECIALFILE.csv')
        }
        response = client.post(
            '/upload-data/carers-allowance/volumetrics',
            data=post_data)

        self.assert_session_contains('upload_problems', ['99'])
        assert_that(response.headers['Location'], ends_with('/error'))
        assert_that(response.status_code, equal_to(302))
        assert_that(data_set_post_patch.called, equal_to(False))

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.list_data_sets')
    def test_data_sets_redirects_to_sign_out_when_403_on_data_set_list(
            self,
            mock_data_set_list,
            client):
        bad_response = requests.Response()
        bad_response.status_code = 403
        http_error = requests.exceptions.HTTPError()
        http_error.response = bad_response
        mock_data_set_list.side_effect = http_error
        response = client.get("/upload-data")
        assert_that(response.status_code, equal_to(302))
        assert_that(
            response.headers['Location'],
            ends_with('/sign-out'))

    @signed_in
    @patch('performanceplatform.client.admin.AdminAPI.list_data_sets')
    def test_data_sets_renders_a_data_set_list_and_okay_message_on_success(
            self,
            mock_data_set_list,
            client):
        mock_data_set_list.return_value = [
            {
                'data_group': "group_1",
                'data_type': "type1"
            },
            {
                'data_group': "group_1",
                'data_type': "type2"
            },
            {
                'data_group': "group_2",
                'data_type': "type3"
            }
        ]
        with self.client.session_transaction() as session:
            session['upload_okay_message'] = {
                'data_group': 'group uploaded to',
                'data_type': 'type uploaded to'
            }
        response = client.get("/upload-data")
        assert_that(
            response.data,
            contains_string("group_1 type1"))
        assert_that(
            response.data,
            contains_string("group_1 type2"))
        assert_that(
            response.data,
            contains_string("group_2 type3"))
        assert_that(
            response.data,
            contains_string(
                "Your data uploaded successfully into the dataset"))
        assert_that(
            response.data,
            contains_string("group uploaded to type uploaded to"))