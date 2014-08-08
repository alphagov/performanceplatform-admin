from admin import app
from flask import jsonify, render_template, session, redirect, url_for
import requests
from performanceplatform.client.admin import AdminAPI
from functools import wraps
from os import getenv

GOVUK_ENV = getenv('GOVUK_ENV', 'development')


def requires_authentication(f):
    @wraps(f)
    def verify_user_logged_in(*args, **kwargs):
        if not signed_in(session):
            return redirect(url_for('root'))
        else:
            admin_client = get_admin_client(session)
            kwargs['admin_client'] = admin_client
            return f(*args, **kwargs)
    return verify_user_logged_in


def get_admin_client(session):
    return AdminAPI(app.config['STAGECRAFT_HOST'],
                    session['oauth_token']['access_token'])


def base_template_context():
    return {
        'environment': {
            'name': GOVUK_ENV,
            'human_name': GOVUK_ENV[:1].upper() + GOVUK_ENV[1:]
        }
    }


def signed_in(session):
    return 'oauth_user' in session and 'oauth_token' in session


@app.route("/sign-out")
def oauth_sign_out():
    session.clear()
    return redirect(app.config['SIGNON_BASE_URL'] + '/users/sign_out')


@app.route("/", methods=['GET'])
def root():
    if signed_in(session):
        return redirect(url_for('data_sets'))
    else:
        return render_template('index.html', **base_template_context())


@app.route("/data-sets", methods=['GET'])
@requires_authentication
def data_sets(admin_client):
    template_context = base_template_context()
    try:
        data_sets = admin_client.list_data_sets()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 403:
            return redirect(url_for('oauth_sign_out'))
        else:
            raise
    template_context.update({
        'user': session['oauth_user'],
        'data_sets': data_sets
    })
    return render_template('data_sets.html', **template_context)


@app.route("/upload-error", methods=['GET'])
@requires_authentication
def upload_error(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })
    return render_template('upload_error.html', **template_context)


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
