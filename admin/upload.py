from admin import app
from admin.files.spreadsheet import Spreadsheet
from admin.helpers import requires_authentication, base_template_context
from flask import (abort, flash, render_template,
                   redirect, request, session, url_for)
from performanceplatform.client.data_set import DataSet
from requests.exceptions import HTTPError


@app.route('/upload-data', methods=['GET'])
@requires_authentication
def upload_list_data_sets(admin_client):
    template_context = base_template_context()
    try:
        data_sets = admin_client.list_data_sets()
    except HTTPError as err:
        if err.response.status_code == 403:
            return redirect(url_for('oauth_sign_out'))
        else:
            raise
    template_context.update({
        'user': session['oauth_user'],
        'data_sets': data_sets
    })
    if 'upload_okay_message' in session:
        upload_okay_message = session['upload_okay_message']
        template_context['upload_okay_message'] = upload_okay_message
    return render_template('data_sets.html', **template_context)


@app.route('/upload-data/<data_group>/<data_type>', methods=['POST'])
@requires_authentication
def upload_post(data_group, data_type, admin_client):
    try:
        data_set_config = admin_client.get_data_set(data_group, data_type)
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
def upload_error(data_group, data_type, admin_client):
    problems = session['upload_problems']
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
        'problems': problems,
        'data_set': {
            'data_group': data_group,
            'data_type': data_type
        }
    })
    return render_template('upload_error.html', **template_context)
