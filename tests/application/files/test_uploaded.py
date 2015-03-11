import os
import unittest

from functools import wraps
from mock import patch
from nose.tools import eq_
from werkzeug.datastructures import FileStorage

from application.files.uploaded import UploadedFile


TEST_FILE_PATH = '/tmp/test-uploaded-file'


class FakeProcess(object):

    def __init__(self, return_code):
        self._returncode = return_code

    def communicate(self):
        self.returncode = self._returncode
        return '', ''


def create_file_storage(content, filename='file.txt',
                        content_type='text/plain',
                        content_length=0):
    with open(TEST_FILE_PATH, 'w') as f:
        f.write(content)

    stream = open(TEST_FILE_PATH, 'r')

    return FileStorage(
        stream=stream,
        filename=TEST_FILE_PATH,
        content_type=content_type,
        content_length=content_length
    )


def stub_virus_scan(is_virus):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            with patch(
                    'application.files.uploaded.UploadedFile.is_virus') as vs:
                vs.return_value = is_virus
                func(*args, **kwargs)
        return wrapped
    return decorator


class TestUploadedFile(unittest.TestCase):

    def tearDown(self):
        if os.path.isfile(TEST_FILE_PATH):
            os.remove(TEST_FILE_PATH)

    @stub_virus_scan(is_virus=False)
    def test_is_empty(self):
        uploaded_file = UploadedFile(create_file_storage(''))

        eq_(uploaded_file.is_empty(), True)
        eq_(uploaded_file.validate(),
            ['File is empty'])

    @stub_virus_scan(is_virus=False)
    def test_is_too_big(self):
        csv_length_1000009 = '\n'.join(['aa,bb,ccc' for i in range(100001)])
        uploaded_file = UploadedFile(create_file_storage(csv_length_1000009))

        eq_(uploaded_file.is_too_big(), True)
        eq_(uploaded_file.validate(),
            ['File is too big (1000009)'])

    @stub_virus_scan(is_virus=False)
    def test_valid_if_good_size(self):
        csv_length_999999 = '\n'.join(['aa,bb,ccc' for i in range(100000)])
        uploaded_file = UploadedFile(create_file_storage(csv_length_999999))

        eq_(uploaded_file.validate(), [])

    @stub_virus_scan(is_virus=False)
    def test_file_gets_cleaned_up(self):
        uploaded_file = UploadedFile(create_file_storage(''))

        eq_(os.path.isfile(uploaded_file.filename), True)
        uploaded_file.cleanup()
        eq_(os.path.isfile(uploaded_file.filename), False)

        with UploadedFile(create_file_storage('')) as with_ufile:
            filename = with_ufile.filename
            eq_(os.path.isfile(with_ufile.filename), True)

        eq_(os.path.isfile(filename), False)

    @patch('application.files.uploaded.Popen')
    def test_virus_scanning(self, mock_Popen):
        mock_Popen.return_value = FakeProcess(0)
        csv_length_999999 = '\n'.join(['aa,bb,ccc' for i in range(100000)])
        uploaded_file = UploadedFile(create_file_storage(csv_length_999999))

        eq_(uploaded_file.validate(), [])

    @patch('application.files.uploaded.Popen')
    def test_virus_scanning_fails_validation(self, mock_Popen):
        mock_Popen.return_value = FakeProcess(1)
        csv_length_999999 = '\n'.join(['aa,bb,ccc' for i in range(100000)])
        uploaded_file = UploadedFile(create_file_storage(csv_length_999999))

        eq_(uploaded_file.validate(), ['File may contain a virus'])
