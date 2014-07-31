from admin import app
from hamcrest import assert_that, is_, equal_to, ends_with
from mock import patch
from StringIO import StringIO
import unittest
from os import path

from pprint import pprint

class UploadTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    @patch('admin.files.uploaded.UploadedFile.is_virus')
    @patch('admin.helpers.get_context')
    @patch('admin.upload.get_data_set_config')
    @patch('performanceplatform.client.data_set.DataSet.post')
    def test_user_can_post_to_upload_data(
            self,
            data_set_post_patch,
            get_data_set_config_patch,
            get_context_patch,
            is_virus_patch):
        is_virus_patch.return_value = False
        get_context_patch.return_value = {'user': {'email': 'test@example.com'}}
        get_data_set_config_patch.return_value = {'bearer_token':'abc123', 'foo': 'bar'}


        response = self.app.post('/upload-data/carers-allowance/volumetrics',
                                     data={'carers-allowance-volumetrics-file': (StringIO('_timestamp,foo\n2014-08-05T00:00:00Z,40'), 'MYSPECIALFILE.csv')})

        print response

        data_set_post_patch.assert_called_once_with([{u'_timestamp': u'2014-08-05T00:00:00Z', u'foo': 40}])

        upload_done_path = '/upload-data/carers-allowance/volumetrics/done'
        assert_that(response.headers['Location'], ends_with(upload_done_path))
        assert_that(response.status_code, equal_to(302))

    @patch('admin.upload.get_data_set_config')
    def test_no_data_set_config_returns_error(self, get_data_set_config_patch):
        get_data_set_config_patch.return_value = None
        response = self.app.post('/upload-data/carers-allowance/volumetrics',
                                 data={'file': (StringIO('data'), 'file.xlsx')})

        assert_that(response.status_code, equal_to(404))

    def test_probem_in_spreadsheet_prevents_post_to_backdrop(self):
        assert_that(1, is_(2))

    def test_no_problems_after_post_flashes_success(self):
        assert_that(1, is_(2))

    def test_problems_after_post_flashes_erorr(self):
        assert_that(1, is_(2))
