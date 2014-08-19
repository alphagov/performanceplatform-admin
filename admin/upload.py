from admin import app
from admin.files.spreadsheet import Spreadsheet
from admin.helpers import(
    requires_authentication,
    base_template_context,
    group_by_group)
from flask import (abort, render_template,
                   redirect, request, session, url_for)
from flask.json import jsonify
from performanceplatform.client.data_set import DataSet
from requests.exceptions import HTTPError
import json


@app.route('/upload-data', methods=['GET'])
@requires_authentication
def upload_list_data_sets(admin_client):
    template_context = base_template_context()
    try:
        data_sets = group_by_group(admin_client.list_data_sets())
    except HTTPError as err:
        if err.response.status_code == 401:
            return redirect(url_for('oauth_sign_out'))
        else:
            raise
    template_context.update({
        'user': session['oauth_user'],
        'data_sets': data_sets
    })
    if 'upload_data' in session:
        upload_data = session.pop('upload_data')
        template_context['upload_data'] = upload_data
    return render_template('data_sets.html', **template_context)


@app.route('/upload-data/<data_group>/<data_type>', methods=['POST'])
@requires_authentication
def upload_post(data_group, data_type, admin_client):
    try:
        data_set = admin_client.get_data_set(data_group, data_type)
    except HTTPError as err:
        return response(500, data_group, data_type,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())])

    if data_set is None:
        abort(
            404,
            'There is no data set of for data-group: {} and data-type: {}'
            .format(data_group, data_type))

    problems, our_problem = upload_spreadsheet(data_set, request.files['file'])
    if len(problems) == 0:
        messages = []
        status = 200
    else:
        messages = problems
        status = 500 if our_problem else 400

    return response(status, data_group, data_type, messages)


def upload_spreadsheet(data_set, file_data):
    problems = []
    our_problem = False

    if len(file_data.filename) == 0:
        problems += ["Please choose a file to upload"]
    else:
        with Spreadsheet(file_data) as spreadsheet:
            problems += spreadsheet.validate()

            if len(problems) == 0:
                url = '{0}/data/{1}/{2}'.format(app.config['BACKDROP_HOST'],
                                                data_set['data_group'],
                                                data_set['data_type'])
                data_set = DataSet(url, data_set['bearer_token'])
                try:
                    data_set.post(spreadsheet.as_json())
                except HTTPError as err:
                    # only 400 errors are actually user errors, anything else
                    # is our fault
                    our_problem = err.response.status_code > 400
                    if err.response.status_code == 400:
                        json_error = err.response.json()
                        if 'messages' in json_error:
                            problems += json_error['messages']
                        else:
                            problems += 'Unknown validation error'
                    else:
                        problems += ['[{}] {}'.format(err.response.status_code,
                                                      err.response.json())]

    return problems, our_problem


def response(status_code, data_group, data_type, payload):
    data = {
        'data_group': data_group,
        'data_type': data_type,
        'payload': payload
    }

    if json_request(request):
        r = jsonify(data)
        r.status_code = status_code
    else:
        session['upload_data'] = data
        r = redirect(url_for('upload_list_data_sets'))

    return r


def json_request(request):
    return request.headers.get('Accept', 'text/html') == 'application/json'
