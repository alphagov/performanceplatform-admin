from application.files.parsers.dsv import parse_csv
from application.files.parsers.excel import parse_excel, is_excel
from application.files.parsers.util import make_dicts
from application.files.uploaded import UploadedFile


class Spreadsheet(UploadedFile):

    ALLOWED_CONTENT_TYPES = [
        'text/plain',
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ]

    def as_json(self):
        json = None

        with open(self.filename) as spreadsheet:
            if is_excel(spreadsheet):
                lines = parse_excel(spreadsheet)
            else:
                lines = parse_csv(spreadsheet)

            json = list(make_dicts(lines))

        return json

    def is_valid_content_type(self):
        return self.content_type in self.ALLOWED_CONTENT_TYPES

    def validate(self):
        problems = super(Spreadsheet, self).validate()

        if not self.is_valid_content_type():
            problems.append(
                'Invalid content type for file "{}"'.format(self.content_type))

        return problems
