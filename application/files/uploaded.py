
import mimetypes
import os

from subprocess import Popen, PIPE
from werkzeug.utils import secure_filename


class FileUploadError(IOError):

    def __init__(self, message):
        self.message = message


class UploadedFile(object):

    # This is ~ 1mb in octets
    MAX_FILE_SIZE = 1000000  # exclusive, so anything >= to this is invalid

    def __init__(self, file_storage):
        filename = os.path.join('/tmp', secure_filename(file_storage.filename))

        try:
            file_storage.save(filename)
        except IOError as e:
            raise FileUploadError(e.message)

        self.filename = filename
        self.file_size = os.path.getsize(filename)
        self.content_type, _ = mimetypes.guess_type(filename)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cleanup()

    def is_virus(self):
        proc = Popen(['clamdscan', self.filename],
                     stdout=PIPE, stderr=PIPE)

        _, stderr = proc.communicate()
        return_code = proc.returncode

        if return_code == 0:    # No virus found
            return False
        elif return_code == 1:  # Virus(es) found
            return True
        else:                   # An error occured
            raise FileUploadError(
                'Error running the virus scanner: {0}'.format(stderr)
            )

    def is_empty(self):
        return self.file_size == 0

    def is_too_big(self):
        return self.file_size >= self.MAX_FILE_SIZE

    def validate(self):
        problems = []

        if self.is_empty():
            problems.append('File is empty')

        if self.is_too_big():
            problems.append('File is too big ({0})'.format(self.file_size))

        if self.is_virus():
            problems.append('File may contain a virus')

        return problems

    def cleanup(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)
