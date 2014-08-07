from flask import Flask
from os import getenv, path
from admin.core import log_handler

app = Flask(__name__)
from flask.ext.scss import Scss

GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app.config['LOG_LEVEL'] = "INFO"
app.config.from_object('admin.config.{0}'.format(GOVUK_ENV))

log_handler.set_up_logging(app, GOVUK_ENV)

app.secret_key = app.config['COOKIE_SECRET_KEY']

import admin.main
import admin.authentication
from redis import Redis
from admin.redis_session import RedisSessionInterface

app.redis_instance = Redis(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT']
)
app.session_interface = RedisSessionInterface(
    redis=app.redis_instance, prefix='admin_app:session:')


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
