from flask import Flask
from os import getenv

app = Flask(__name__)

GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app.config.from_object('admin.config.{0}'.format(GOVUK_ENV))
app.secret_key = app.config['COOKIE_SECRET_KEY']

import admin.main
import admin.authentication


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)
