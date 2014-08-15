from admin import app
from admin.helpers import (
    signed_in,
    base_template_context,
    signed_in_no_access
)
from flask import (
    jsonify, render_template, session, redirect,
    url_for, make_response
)
import requests
from admin.authentication import get_authorization_url


@app.route("/", methods=['GET'])
def root():
    if signed_in(session):
        return redirect(url_for('upload_list_data_sets'))
    elif signed_in_no_access(session):
        template_context = base_template_context()
        template_context.update({
            'user': session['oauth_user']
        })
        return render_template('index.html', **template_context)
    else:
        return redirect(get_authorization_url(session))


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
