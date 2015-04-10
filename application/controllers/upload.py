from application import app
from application.files.spreadsheet import Spreadsheet
from application.forms import UploadDataForm
from application.helpers import(
    requires_authentication,
    base_template_context,
    group_by_group, requires_permission)
from flask import (abort, render_template,
                   redirect, request, session, url_for)
from flask.json import jsonify
from performanceplatform.client.data_set import DataSet
from requests.exceptions import HTTPError


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


def get_messages_and_status_for_problems(our_problem, problems):
    if len(problems) == 0:
        messages = []
        status = 200
    else:
        messages = problems
        status = 500 if our_problem else 400
    return messages, status


@app.route('/upload-data/<data_group>/<data_type>', methods=['POST'])
@requires_authentication
def upload_post(data_group, data_type, admin_client):
    try:
        data_set = admin_client.get_data_set(data_group, data_type)
    except HTTPError as err:
        return response(500, data_group, data_type,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_list_data_sets'))

    if data_set is None:
        abort(
            404,
            'There is no data set of for data-group: {} and data-type: {}'
            .format(data_group, data_type))

    problems, our_problem = upload_spreadsheet(data_set, request.files['file'])
    messages, status = get_messages_and_status_for_problems(our_problem,
                                                            problems)

    return response(status, data_group, data_type, messages,
                    url_for('upload_list_data_sets'))


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
                            problems += 'Unknown validation error: {}'.format(
                                json_error
                            )
                    else:
                        problems += ['[{}] {}'.format(err.response.status_code,
                                                      err.response.json())]

    return problems, our_problem


def response(status_code, data_group, data_type, payload, redirect_url_for):
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
        r = redirect(redirect_url_for)

    return r


def json_request(request):
    return request.headers.get('Accept', 'text/html') == 'application/json'


@app.route('/dashboard/<uuid>/digital-take-up/upload',
           methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def upload_digital_take_up_data_file(admin_client, uuid):
    DATA_TYPE_NAME = 'transactions-by-channel'
    template_context = base_template_context()

    return render_template('digital_take_up/upload.html',
                           uuid=uuid,
                           data_type=DATA_TYPE_NAME,
                           **template_context)


def get_or_create_data_set(admin_client, uuid, data_group, data_type,
                           data_set_config):
    try:
        data_set = admin_client.get_data_set(
            data_group, data_type)
    except HTTPError as err:
        return response(500, data_group, data_type,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_digital_take_up_data_file',
                                uuid=uuid))

    if not data_set:
        data_set = admin_client.create_data_set(data_set_config)

    return data_set


def create_module_if_not_exists(admin_client, data_group, module_config, module_type_name):
    module_types = admin_client.list_module_types()
    for module_type in module_types:
        if module_type['name'] == module_type_name:
            module_config["type_id"] = module_type['id']
    try:
        admin_client.add_module_to_dashboard(
            data_group, module_config)
    except HTTPError as e:
        exists = "Module with this Dashboard and Slug already exists"
        if exists not in e.response.text:
            raise


@app.route('/dashboard/<uuid>/digital-take-up/upload',
           methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_data_file_to_dashboard(admin_client, uuid):
    DATA_TYPE_NAME = 'transactions-by-channel'
    template_context = base_template_context()

    dashboard = admin_client.get_dashboard(uuid)
    data_group = dashboard["slug"]

    data_set_config = {
        'data_type': DATA_TYPE_NAME,
        'data_group': data_group,
        'bearer_token': 'abc123',
        'upload_format': 'csv',
        'auto_ids': '_timestamp, period, channel',
        'max_age_expected': 1300000
    }

    data_set = get_or_create_data_set(
        admin_client, uuid, data_group, DATA_TYPE_NAME, data_set_config)

    module_config = {
        "data_set": data_set["name"],
        "data_group": data_group,
        "data_type": data_set["data_type"],
        "slug": "digital-takeup",
        "title": "Digital take-up",
        "description": "What percentage of transactions were completed "
                       "using the online service",
        "info": ["Data source: Department for Work and Pensions",
                 "<a href='/service-manual/measurement/digital-takeup' "
                 "rel='external'>Digital take-up</a> measures the "
                 "percentage of completed applications that are made "
                 "through a digital channel versus non-digital channels."],
        "options": {
            "value-attribute": "count:sum",
            "axis-period": "month",
            "axes": {"y": [{
                               "format": "percent",
                               "key": "completion",
                               "label": "Digital take-up"
            }],
                "x": {
                "format": "date",
                "key": ["_start_at", "_end_at"],
                "label": "Date"
            }
            },
            "numerator-matcher": "(digital)",
            "denominator-matcher": ".+",
            "matching-attribute": "channel"
        },
        "query_parameters": {
            "collect": ["count:sum"],
            "group_by": ["channel"],
            "period": "month"
        },
        "order": 1
    }

    create_module_if_not_exists(
        admin_client, data_group, module_config, 'completion_rate')

    # problems, our_problem = \
    #     upload_spreadsheet(data_set, request.files['file'])
    #
    # messages, status = get_messages_and_status_for_problems(our_problem,
    #                                                         problems)
    #
    # return response(status, data_group, DATA_TYPE_NAME, messages,
    #                 url_for('upload_digital_take_up_data_success',
    #                         data_group=data_group))

    return upload_post(data_group, DATA_TYPE_NAME)


@app.route('/dashboard/<data_group>/digital-take-up/upload/success',
           methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_digital_take_up_data_success(admin_client, data_group):
    template_context = base_template_context()
    return render_template('digital_take_up/upload_success.html',
                           data_group=data_group,
                           **template_context)
