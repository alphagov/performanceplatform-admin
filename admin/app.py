from flask import Flask, jsonify
from os import getenv


GOVUK_ENV = getenv('GOVUK_ENV', 'development')

app = Flask(__name__)

app.config.from_object('admin.config.{0}'.format(GOVUK_ENV))


@app.route("/", methods=['GET'])
def root():
    return "Application root"


@app.route("/_status", methods=['GET'])
def status():
    return jsonify({"admin": "ok"})


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)
