from flask import Flask
from flask.ext.scss import Scss
from flask_wtf.csrf import CsrfProtect
from os import getenv, path
from raven.contrib.flask import Sentry
from redis import Redis

from application.core import log_handler
from application.redis_session import RedisSessionInterface

app = Flask(__name__)

GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app.config['LOG_LEVEL'] = "INFO"
app.config.from_object('application.config.{0}'.format(GOVUK_ENV))
app.secret_key = app.config['COOKIE_SECRET_KEY']
app.redis_instance = Redis(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT'],
)
app.session_interface = RedisSessionInterface(
    redis=app.redis_instance, prefix='admin_app:session:')

# adds uncaught exception handlers to app and submits to sentry
# this will only send when SENTRY_DSN is defined in config
Sentry(app)

csrf = CsrfProtect(app)

log_handler.set_up_logging(app, GOVUK_ENV)


import application.controllers.main
import application.controllers.authentication
import application.controllers.admin.dashboards
import admin.registrations
import application.controllers.admin.transforms
import application.controllers.upload


def start(port):
    app.debug = app.config['DEBUG'] or False
    if app.debug:
        # does not watch for changes and recompile on requests if debug false
        Scss(app,
             static_dir='application/static/css',
             asset_dir='application/assets/scss/manifest',
             load_paths=[
                 path.join(path.dirname(__file__), 'assets/scss')])
    app.run('0.0.0.0', port=port)
