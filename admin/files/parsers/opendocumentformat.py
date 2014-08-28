from admin.files.parsers import ParseError

import datetime
import logging
import pytz
import odf.namespaces as namespaces
import odf.opendocument as opendocument
import odf.table as table


class OdfError(ParseError):

    def __init__(self, description):
        self.description = description

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.description == other.description

    def __ne__(self, other):
        return not self.__eq__(other)

ODF_ERROR = OdfError("error in cell")


def is_odf(incoming_data):
    matches_odf = False
    try:
        doc = opendocument.load(incoming_data)
        matches_odf = (doc.spreadsheet and len(doc.spreadsheet.getElementsByType(table.Table)) > 0)
    except:
        logging.warning('File is not an odf spreadsheet')

    incoming_data.seek(0)
    return matches_odf


def parse_odf(incoming_data):
    doc = opendocument.load(incoming_data)

    return [row for row in _extract_rows(doc.spreadsheet.getElementsByType(table.Table)[0]) if len(row) > 0]

def _extract_rows(table_sheet):
    return [_extract_values(row) for row in table_sheet.getElementsByType(table.TableRow) if row.getElementsByType(table.TableCell)]


def _extract_values(row):
    return [_extract_cell_value(cell) for cell in row.getElementsByType(table.TableCell) if cell.getAttrNS(namespaces.OFFICENS, 'value-type')]


def _extract_cell_value(cell):
    value = None

    def float_conversion(c):
        try:
            v = int(str(c))
        except:
            v = float(str(c))
        return v

    def date_conversion(c):
        v = c.getAttrNS(namespaces.OFFICENS, 'date-value')
        d = None
        try:
            d = datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S')
        except:
            d = datetime.datetime.strptime(v, '%Y-%m-%d')
        return d.replace(tzinfo=pytz.UTC).isoformat()

    value_extractors = {
        "date":date_conversion,
        "string":lambda c: str(c),
        "float":float_conversion
    }

    err = cell.getAttrNS("urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0", 'value-type')

    if err and err == "error":
        return ODF_ERROR

    value_type = cell.getAttrNS(namespaces.OFFICENS, 'value-type')

    if value_extractors.has_key(value_type):
        value = value_extractors[value_type](cell)
    else:
        print "No extractor for value_type: %s" % (value_type)

    return value
