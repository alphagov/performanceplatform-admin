from admin.files.parsers.opendocumentformat import parse_odf, ODF_ERROR

import os
import unittest

from hamcrest import assert_that, contains, instance_of


def fixture_path(name):
    return os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..', '..', 'fixtures', name))


class ParseodfTestCase(unittest.TestCase):
    def _parse_odf(self, file_name):
        file_stream = open(fixture_path(file_name))
        return parse_odf(file_stream)

    def test_parse_an_odf_file(self):
        assert_that(self._parse_odf("data.ods"), contains(
            ["name", "age", "nationality"],
            ["Pawel", 27, "Polish"],
            ["Max", 35, "Italian"],
        ))

    def test_parse_types(self):
        rows = self._parse_odf("types.ods")

        assert_that(rows[1][1], instance_of(int))
        assert_that(rows[1][2], instance_of(float))
        assert_that(rows, contains(
            ["string", "int", "float"],
            ["foobar", 10, 10.5]
        ))

    def test_parse_odf_dates(self):
        assert_that(self._parse_odf("dates.ods"), contains(
            ["date"],
            ["2013-12-03T13:30:00+00:00"],
            ["2013-12-04T00:00:00+00:00"],
        ))

    def test_parse_odf_file(self):
        assert_that(self._parse_odf("odsfile.ods"), contains(
            ["date", "name", "number"],
            ["2013-12-03T13:30:00+00:00", "test1", 12],
            ["2013-12-04T00:00:00+00:00", "test2", 34],
        ))

    def test_parse_odf_with_error(self):
        assert_that(self._parse_odf("error.ods"), contains(
            ["date", "name", "number", "error"],
            ["2013-12-03T13:30:00+00:00", "test1", 12, ODF_ERROR],
            ["2013-12-04T00:00:00+00:00", "test2", 34, ODF_ERROR],
        ))

    def test_parse_odf_with_multiple_sheets_only_gets_first(self):
        assert_that(self._parse_odf("multiple_sheets.ods"), contains(
            ["Sheet 1 content"],
            ["Nothing exciting"]
        ))

    def test_parse_odf_handle_empty_cells_and_lines(self):
        assert_that(self._parse_odf("empty_cell_and_row.ods"), contains(
            ["Next cell is none", None, "Previous cell is none"],
            [None, None, None],
            ["The above row", "is full", "of nones"]
        ))
