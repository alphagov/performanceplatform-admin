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
        session_context = get_context(session)
        if 'user' not in session_context:
            return redirect(url_for('root'))
        kwargs['session_context'] = session_context
        return f(*args, **kwargs)
    return verify_user_logged_in


# this is doing too much or should it have the signon_base_url stuff too
def get_context(session):
    context = dict()

    if 'oauth_user' in session and 'oauth_token' in session:
        admin_client = AdminAPI(app.config['STAGECRAFT_HOST'],
                                session['oauth_token']['access_token'])
        try:
            context = {
                'user': session['oauth_user'],
                'data_sets': admin_client.list_data_sets()
            }
        except requests.exceptions.RequestException as e:
            if not e.response.status_code == 403:
                raise
    context['environment'] = environment_dict()

    return context


def environment_dict():
    return {
        'name': GOVUK_ENV,
        'human_name': GOVUK_ENV[:1].upper() + GOVUK_ENV[1:]
    }


@app.route("/sign-out")
def oauth_sign_out():
    session.clear()
    return redirect(app.config['SIGNON_BASE_URL'] + '/users/sign_out')


@app.route("/", methods=['GET'])
def root():
    session_context = get_context(session)
    if 'user' in get_context(session):
        return redirect(url_for('data_sets'))
    else:
        return render_template('index.html', **session_context)


@app.route("/data-sets", methods=['GET'])
@requires_authentication
def data_sets(session_context=None):
    return render_template('data_sets.html', **session_context)


@app.route("/upload-error", methods=['GET'])
@requires_authentication
def upload_error(session_context=None):
    return render_template('upload_error.html', **session_context)


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
