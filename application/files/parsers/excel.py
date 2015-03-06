from application.files.parsers import ParseError

import datetime
import logging
import pytz
import xlrd


class ExcelError(ParseError):

    def __init__(self, description):
        self.description = description

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.description == other.description

    def __ne__(self, other):
        return not self.__eq__(other)

EXCEL_ERROR = ExcelError("error in cell")


def is_excel(incoming_data):
    matches_excel = False
    try:
        book = xlrd.open_workbook(file_contents=incoming_data.read())
        book.sheet_by_index(0)
        matches_excel = True
    except xlrd.XLRDError:
        logging.warning('File is not an excel spreadsheet')

    incoming_data.seek(0)
    return matches_excel


def parse_excel(incoming_data):
    book = xlrd.open_workbook(file_contents=incoming_data.read())

    return _extract_rows(book.sheet_by_index(0), book)


def _extract_rows(sheet, book):
    return [_extract_values(sheet.row(i), book) for i in range(sheet.nrows)]


def _extract_values(row, book):
    return [_extract_cell_value(cell, book) for cell in row]


def _extract_cell_value(cell, book):
    value = None
    if cell.ctype == xlrd.XL_CELL_DATE:
        time_tuple = xlrd.xldate_as_tuple(cell.value, book.datemode)
        dt = datetime.datetime(*time_tuple)
        value = dt.replace(tzinfo=pytz.UTC).isoformat()
    elif cell.ctype == xlrd.XL_CELL_NUMBER:
        value = cell.value
        if value == int(value):
            value = int(value)
    elif cell.ctype == xlrd.XL_CELL_EMPTY:
        value = None
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        logging.warn("Encountered errors in cells when parsing excel file")
        value = EXCEL_ERROR
    else:
        value = cell.value

    return value
