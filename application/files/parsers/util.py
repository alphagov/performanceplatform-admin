from application.files.parsers import ParseError
from dateutil.parser import parse

import pytz


def remove_blanks(rows):
    def blank_filter(r):
        return not all(v is None or
                       (isinstance(v, basestring) and len(v) == 0) for v in r)

    return filter(blank_filter, rows)


def make_dicts(rows):
    """Return an iterator of dictionaries given an iterator of rows

    Given an iterator of rows consisting of a iterator of lists of values
    produces an iterator of dictionaries using the first row as the keys for
    all subsequent rows.
    """
    rows = iter(rows)
    keys = next(rows)

    for row in remove_blanks(rows):
        key_count = len(keys)
        row_count = len(row)
        if key_count < row_count:
            raise ParseError(
                'Some rows in the CSV file contain more values than columns')
        if key_count > row_count:
            raise ParseError(
                'Some rows in the CSV file contain fewer values than columns')

        yield dict(zip(keys, row))


def format_utc_date(cell):
    if cell:
        try:
            dt = parse(cell)
            return dt.replace(tzinfo=pytz.UTC).isoformat()
        except ValueError:
            return cell
    else:
        return cell
