from admin import app
from flask import jsonify, render_template, session
import requests
from performanceplatform.client.admin import AdminAPI


def get_context(session):
    context = dict()

    if 'oauth_user' in session and 'oauth_token' in session:
        admin_client = AdminAPI(app.config['STAGECRAFT_HOST'],
                                session['oauth_token']['access_token'])
        context = {
            'user': session['oauth_user'],
            'data_sets': admin_client.list_data_sets(),
        }

    return context


@app.route("/", methods=['GET'])
def root():
    return render_template('index.html')


@app.route("/data-sets", methods=['GET'])
def data_sets():
    return render_template('data_sets.html', **get_context(session))


@app.route("/upload-error", methods=['GET'])
def upload_error():
    return render_template('upload_error.html')


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
