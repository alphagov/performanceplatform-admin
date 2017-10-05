from os import getenv, path

from flask import Flask
from flask.ext.scss import Scss
from flask_wtf.csrf import CsrfProtect
from raven.contrib.flask import Sentry
from redis import Redis

from application.core import log_handler
from application.redis_session import RedisSessionInterface

app = Flask(__name__)

GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app.config['LOG_LEVEL'] = "INFO"
app.config.from_object('application.config.default')
app.config.from_object('application.config.{0}'.format(GOVUK_ENV))
app.secret_key = app.config['SECRET_KEY']
app.redis_instance = Redis.from_url(url=app.config['REDIS_URL'])
print('---- {}'.format(app.redis_instance.connection_pool))
app.session_interface = RedisSessionInterface(
    redis=app.redis_instance, prefix='performanceplatform_admin:session:')

# adds uncaught exception handlers to app and submits to sentry
# this will only send when SENTRY_DSN is defined in config
Sentry(app)

csrf = CsrfProtect(app)

log_handler.set_up_logging(app, GOVUK_ENV)


import application.controllers.main
import application.controllers.authentication
import application.controllers.admin.dashboards
import application.controllers.registrations
import application.controllers.dashboards
import application.controllers.builder.user_satisfaction
import application.controllers.builder.digital_take_up
import application.controllers.builder.cost_per_transaction
import application.controllers.upload


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


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
