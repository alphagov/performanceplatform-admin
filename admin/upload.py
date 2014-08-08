from admin import app
from admin.files.spreadsheet import Spreadsheet
from admin.helpers import requires_authentication
from flask import (abort, flash, render_template,
                   redirect, request, session, url_for)
from performanceplatform.client.admin import AdminAPI
from performanceplatform.client.data_set import DataSet
from requests.exceptions import HTTPError


@app.route('/upload-data', methods=['GET'])
@requires_authentication
def upload_list_data_sets(session_context=None):
    if 'upload_okay_message' in session:
        session_context['upload_okay_message'] = session.pop(
            'upload_okay_message')
    return render_template('data_sets.html', **session_context)


@app.route('/upload-data/<data_group>/<data_type>', methods=['POST'])
@requires_authentication
def upload_post(data_group, data_type, session_context=None):
    try:
        data_set_config = get_data_set_config(data_group, data_type)
    except HTTPError as err:
        flash(build_http_flash(err, "Stagecraft"))
        return redirect(url_for('upload_list_data_sets'))

    if data_set_config is None:
        abort(
            404,
            'There is no data set of for data-group: {} and data-type: {}'
            .format(data_group, data_type))

    html_file_identifier = '{0}-{1}-file'.format(data_group, data_type)

    problems = []

    file_data = request.files[html_file_identifier]
    if len(file_data.filename) == 0:
        flash("Please choose a file to upload")
        return redirect(url_for('upload_list_data_sets'))

    with Spreadsheet(file_data) as spreadsheet:
        problems += spreadsheet.validate()

        if len(problems) == 0:
            url = '{0}/data/{1}/{2}'.format(app.config['BACKDROP_HOST'],
                                            data_group, data_type)
            data_set = DataSet(url, data_set_config['bearer_token'])
            try:
                data_set.post(spreadsheet.as_json())
                session['upload_okay_message'] = {
                    'data_group': data_group,
                    'data_type': data_type}
            except HTTPError as err:
                flash(build_http_flash(err, "Backdrop"))
            return redirect(url_for('upload_list_data_sets'))
        else:
            session['upload_problems'] = problems
            return redirect(url_for('upload_error',
                                    data_group=data_group,
                                    data_type=data_type))


def build_http_flash(err, app_name):
    return '{} returned status code <{}> with json: {}'.format(
        app_name,
        err.response.status_code,
        err.response.json())


@app.route("/upload-data/<data_group>/<data_type>/error", methods=['GET'])
@requires_authentication
def upload_error(data_group, data_type, session_context=None):
    problems = session.pop('upload_problems')
    session_context.update({
        'problems': problems,
        'data_set': {
            'data_group': data_group,
            'data_type': data_type}})
    return render_template('upload_error.html', **session_context)


def get_data_set_config(data_group, data_type):
    admin_client = AdminAPI(app.config['STAGECRAFT_HOST'],
                            session['oauth_token']['access_token'])

    return admin_client.get_data_set(data_group, data_type)
