from flask import Flask, jsonify
from os import getenv
import requests


GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app = Flask(__name__)

app.config.from_object('admin.config.{0}'.format(GOVUK_ENV))


@app.route("/", methods=['GET'])
def root():
    return "Application root"


@app.route("/_status", methods=['GET'])
def status():
    app_status = {'admin': {'status': 'ok'}}
    error_status = {'status': 'error'}

    try:
        backdrop_status = requests.get(
            "{0}/_status".format(app.config['BACKDROP_HOST']))
        if backdrop_status.status_code == 200:
            app_status['backdrop'] = backdrop_status.json()
        else:
            app_status['backdrop'] = error_status
    except requests.exceptions.RequestException:
        app_status['backdrop'] = error_status

    try:
        stagecraft_status = requests.get(
            "{0}/_status".format(app.config['STAGECRAFT_HOST']))
        if stagecraft_status.status_code == 200:
            app_status['stagecraft'] = stagecraft_status.json()
        else:
            app_status['stagecraft'] = error_status
    except requests.exceptions.RequestException:
        app_status['stagecraft'] = error_status

    return jsonify(app_status)


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)
