from application.files.parsers import ParseError

import csv
import itertools
from application.files.parsers.util import format_utc_date


def parse_csv(incoming_data):
    reader = unicode_csv_reader(
        ignore_comment_lines(lines(incoming_data)), "utf-8")
    return parse_cells_as_numbers(
        ignore_empty_rows(
            ignore_comment_column(reader)))


def lines(stream):
    for candidate_line in stream:
        for line in candidate_line.splitlines(True):
            yield line


def ignore_empty_rows(rows):
    return itertools.ifilterfalse(is_empty_row, rows)


def is_empty_row(row):
    """Returns True if all cells in a row evaluate to False

    >>> is_empty_row(['', False, ''])
    True
    >>> is_empty_row(['', 'a', ''])
    False
    """
    return not any(row)


def parse_cells_as_numbers(rows):
    return [[parse_as_number(cell) for cell in row] for row in rows]


def parse_as_number(cell):
    """Convert a string to an int or a float if it can be

    >>> parse_as_number("1")
    1
    >>> parse_as_number("1.1")
    1.1
    >>> parse_as_number("foo")
    'foo'
    >>> parse_as_number("2015-10-05T00:00:00")
    '2015-10-05T00:00:00+00:00'
    >>> parse_as_number("2015-10-05T00:00:00Z")
    '2015-10-05T00:00:00+00:00'
    """

    try:
        return int(cell)
    except ValueError:
        try:
            return float(cell)
        except ValueError:
            return format_utc_date(cell)


def ignore_comment_lines(reader):
    for line in reader:
        if not line.startswith('#'):
            yield line


def ignore_comment_column(rows):
    rows = iter(rows)
    keys = next(rows)
    index = None

    if "comment" in keys:
        index = keys.index("comment")
        keys = keys[:index] + keys[index + 1:]

    yield keys

    for row in rows:
        if index is not None:
            yield row[:index] + row[index + 1:]
        else:
            yield row


def unicode_csv_reader(incoming_data, encoding):
    reader = csv.reader(incoming_data)

    try:
        for row in reader:
            yield [unicode(cell, encoding) for cell in row]
    except UnicodeError:
        raise ParseError("Non-UTF8 characters found.")
