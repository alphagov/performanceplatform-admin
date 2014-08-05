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

    with Spreadsheet(request.files[html_file_identifier]) as spreadsheet:
        problems += spreadsheet.validate()

        if len(problems) == 0:
            print spreadsheet.as_json()
            url = '{0}/data/{1}/{2}'.format(app.config['BACKDROP_HOST'],
                                            data_group, data_type)
            data_set = DataSet(url, data_set_config['bearer_token'])
            try:
                data_set.post(spreadsheet.as_json())
            except HTTPError as err:
                flash(build_http_flash(err, "Backdrop"))
                return redirect(url_for('upload_list_data_sets'))
    # except virus as err:
    # except invalid as err:
        # problems.append(err.message)

    session['upload_problems'] = problems

    return redirect(url_for('upload_done',
                            data_group=data_group,
                            data_type=data_type))


def build_http_flash(err, app_name):
    return '{} returned status code <{}> with json: {}'.format(
        app_name,
        err.response.status_code,
        err.response.json())


@app.route('/upload-data/<data_group>/<data_type>/done', methods=['GET'])
@requires_authentication
def upload_done(data_group, data_type, session_context=None):
    problems = session['upload_problems']

    success_message = ' '.join([
        'Your data uploaded successfully into the dataset',
        '{0} {1}.'.format(data_group, data_type),
        'In about 20 minutes your data will appear on your dashboard.',
    ])

    error_message = ' '.join([
        'There\'s a problem with your data.',
        'We tried to upload your data into the dataset',
        '{0} {1},'.format(data_group, data_type),
        'but there were the following problems:',
    ] + problems)

    if len(problems) == 0:
        flash(success_message, 'success')
    else:
        flash(error_message, 'danger')

    return redirect(url_for('upload_list_data_sets'))


def get_data_set_config(data_group, data_type):
    admin_client = AdminAPI(app.config['STAGECRAFT_HOST'],
                            session['oauth_token']['access_token'])

    return admin_client.get_data_set(data_group, data_type)
