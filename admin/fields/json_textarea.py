try:
    from html import escape
except ImportError:
    from cgi import escape

from wtforms import StringField
from wtforms.compat import text_type
from wtforms.widgets import html_params, HTMLString

import json


class JSONTextArea(object):

    """
    Renders a textarea element which contains JSON data that has been
    pretty-printed.
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        field_as_string = text_type(field._value())
        try:
            pretty_printed_string = json.dumps(
                json.loads(field_as_string), indent=4, sort_keys=True)
        except ValueError:
            pretty_printed_string = field_as_string
        return HTMLString('<textarea %s>%s</textarea>' % (
            html_params(name=field.name, **kwargs),
            escape(pretty_printed_string, quote=False)
        ))


class JSONTextAreaField(StringField):

    """
    This field represents an HTML ``<textarea>`` which is used to pretty-print
    JSON to make it easier to edit.
    """
    widget = JSONTextArea()
