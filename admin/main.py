from admin import app
from admin.helpers import (
    signed_in,
    base_template_context
)
from flask import (
    jsonify, render_template, session, redirect,
    url_for, make_response
)
import requests


@app.route("/sign-out")
def oauth_sign_out():
    session.clear()
    return redirect(app.config['SIGNON_BASE_URL'] + '/users/sign_out')


@app.route("/", methods=['GET'])
def root():
    if signed_in(session):
        return redirect(url_for('upload_list_data_sets'))
    else:
        return render_template('index.html', **base_template_context())


def check_status(base_url):
    try:
        r = requests.get("{0}/_status".format(base_url))
        status = r.json() if r.status_code == 200 else {'status': 'error'}
    except requests.exceptions.RequestException:
        status = {'status': 'error'}

    return status


@app.route("/_status", methods=['GET'])
def status():
    app_status = {
        'backdrop': check_status(app.config['BACKDROP_HOST']),
        'stagecraft': check_status(app.config['STAGECRAFT_HOST'])
    }

    deps_ok = all(status.get('status', '') == 'ok'
                  for status in app_status.values())

    app_status['status'] = 'ok' if deps_ok else 'error'

    return make_response(
        jsonify(app_status),
        200 if deps_ok else 503
    )
