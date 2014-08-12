from flask import Flask
from flask.ext.scss import Scss
from os import getenv, path
from raven.contrib.flask import Sentry

from admin.core import log_handler

app = Flask(__name__)

GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app.config['LOG_LEVEL'] = "INFO"
app.config.from_object('admin.config.{0}'.format(GOVUK_ENV))
app.secret_key = app.config['COOKIE_SECRET_KEY']

# adds uncaught exception handlers to app and submits to sentry
# this will only send when SENTRY_DSN is defined in config
Sentry(app)

log_handler.set_up_logging(app, GOVUK_ENV)


import admin.main
import admin.authentication
import admin.upload


def start(port):
    app.debug = app.config['DEBUG'] or False
    if app.debug:
        # does not watch for changes and recompile on requests if debug false
        Scss(app,
             static_dir='admin/static/css',
             asset_dir='admin/assets/scss/manifest',
             load_paths=[
                 path.join(path.dirname(__file__), 'assets/scss')])
    app.run('0.0.0.0', port=port)
