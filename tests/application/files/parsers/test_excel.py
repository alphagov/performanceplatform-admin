from application.files.parsers.excel import parse_excel, EXCEL_ERROR

import os
import unittest

from hamcrest import assert_that, contains, instance_of


def fixture_path(name):
    return os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..', '..', 'fixtures', name))


class ParseExcelTestCase(unittest.TestCase):

    def _parse_excel(self, file_name):
        file_stream = open(fixture_path(file_name))
        return parse_excel(file_stream)

    def test_parse_an_xlsx_file(self):
        assert_that(self._parse_excel("data.xlsx"), contains(
            ["name", "age", "nationality"],
            ["Pawel", 27, "Polish"],
            ["Max", 35, "Italian"],
        ))

    def test_parse_types(self):
        rows = self._parse_excel("types.xls")

        assert_that(rows[1][1], instance_of(int))
        assert_that(rows[1][2], instance_of(float))
        assert_that(rows, contains(
            ["string", "int", "float"],
            ["foobar", 10, 10.5]
        ))

    def test_parse_xlsx_dates(self):
        assert_that(self._parse_excel("dates.xlsx"), contains(
            ["date"],
            ["2013-12-03T13:30:00+00:00"],
            ["2013-12-04T00:00:00+00:00"],
        ))

    def test_parse_xls_file(self):
        assert_that(self._parse_excel("xlsfile.xls"), contains(
            ["date", "name", "number"],
            ["2013-12-03T13:30:00+00:00", "test1", 12],
            ["2013-12-04T00:00:00+00:00", "test2", 34],
        ))

    def test_parse_xlsx_with_error(self):
        assert_that(self._parse_excel("error.xlsx"), contains(
            ["date", "name", "number", "error"],
            ["2013-12-03T13:30:00+00:00", "test1", 12, EXCEL_ERROR],
            ["2013-12-04T00:00:00+00:00", "test2", 34, EXCEL_ERROR],
        ))

    def test_parse_xlsx_with_multiple_sheets_only_gets_first(self):
        assert_that(self._parse_excel("multiple_sheets.xlsx"), contains(
            ["Sheet 1 content"],
            ["Nothing exciting"]
        ))

    def test_parse_xlsx_handle_empty_cells_and_lines(self):
        assert_that(self._parse_excel("empty_cell_and_row.xlsx"), contains(
            ["Next cell is none", None, "Previous cell is none"],
            [None, None, None],
            ["The above row", "is full", "of nones"]
        ))

    def test_parse_xlsx_handles_dates_in_text_format(self):
        assert_that(self._parse_excel("bad_dates.xlsx"), contains(
            ["_timestamp", "period", "count"],
            ["2015-10-05T00:00:00+00:00", "week", 1],
            ["2015-10-05T00:00:00+00:00", "week", 100],
            ["2015-10-12T00:00:00+00:00", "week", 2],
            ["2015-10-12T00:00:00+00:00", "week", 200],
        ))
