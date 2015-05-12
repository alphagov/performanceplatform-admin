from requests import HTTPError

from flask import (
    session,
    render_template,
    make_response,
    url_for
)

from application import app
from application.controllers.upload import (
    response,
    upload_file_and_get_status
)
from application.helpers import (
    base_template_context,
    generate_bearer_token,
    requires_authentication,
    requires_permission
)
from application.utils.datetimeutil import (
    previous_year_quarters,
    end_of_quarter
)


DATA_TYPE = 'cost-per-transaction'


def get_module_config_for_cost_per_transaction(owning_organisation):
    module_config = {
        "slug": DATA_TYPE,
        "title": "Cost per transaction",
        "module-type": "bar_chart_with_number",
        "value-attribute": "count",
        "description": "",
        "info": ["Data source: {}".format(owning_organisation),
                 "<a href=\"https://www.gov.uk/service-manual/measurement/\
                cost-per-transaction\">Cost per transaction</a> is the \
                average cost of providing each successfully completed \
                transaction, across all channels. Staff, IT and accommodation \
                costs should be included."],
        "format": {
            "pence": True,
            "type": "currency"
        },
        "query_parameters": {
            "sort_by": "_timestamp:descending"
        },
        "options": {
            "value-attribute": "count",
            "axis-period": "quarter",
            "format": {
                "sigfigs": 4,
                "type": "currency"
            }
        },
        "order": 3,
    }
    return module_config


def get_or_create_data_group(admin_client, data_group_name, data_type, uuid):
    data_group_config = {"name": data_group_name}

    try:
        data_group = admin_client.get_data_group(data_group_name)
    except HTTPError as err:
        return response(500, data_group_config, data_type,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_cost_per_transaction',
                                uuid=uuid))
    if not data_group:
        data_group = admin_client.create_data_group(data_group_config)

    return data_group


def get_or_create_data_set(admin_client, uuid, data_group, data_type):

    data_set_config = get_data_set_config(data_group, data_type)

    try:
        data_set = admin_client.get_data_set(
            data_group, data_type)
    except HTTPError as err:
        return response(500, data_group, data_type,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_cost_per_transaction',
                                uuid=uuid))

    if not data_set:
        data_set = admin_client.create_data_set(data_set_config)
    return data_set


def get_data_set_config(data_group_name, data_type):

    data_set_config = {
        'data_type': data_type,
        'data_group': data_group_name,
        'bearer_token': generate_bearer_token(),
        'upload_format': 'csv',
        'max_age_expected': 0
    }
    return data_set_config


def create_module_if_not_exists(admin_client,
                                data_group,
                                data_type,
                                module_config,
                                module_type_name):
    module_config.update({
        "data_group": data_group,
        "data_type": data_type
    })

    module_types = admin_client.list_module_types()
    for module_type in module_types:
        if module_type['name'] == module_type_name:
            module_config['type_id'] = module_type['id']
    try:
        module = admin_client.add_module_to_dashboard(
            data_group, module_config)
        return module
    except HTTPError as e:
        exists = "Module with this Dashboard and Slug already exists"
        if exists not in e.response.text:
            raise


def create_dataset_and_module(input_data_type, admin_client, uuid, period,
                              module_type, module_config, data_group_name,
                              output_data_type=None):

    data_group = get_or_create_data_group(admin_client, data_group_name,
                                          input_data_type, uuid)
    get_or_create_data_set(admin_client, uuid, data_group['name'],
                           input_data_type)

    create_module_if_not_exists(admin_client, data_group['name'],
                                input_data_type, module_config, module_type)

    session['module'] = module_config['title']


def make_csv():
    """
    Produce a CSV with dates for the last four quarters.
    """

    csv = "_timestamp,end_at,period,channel,count,comment\n"

    quarters = previous_year_quarters()
    for quarter_start in quarters:
        quarter_end = end_of_quarter(quarter_start)
        csv += '{0},{1},{2},{3},{4},{5}\n'.\
            format(quarter_start.isoformat(), quarter_end.isoformat(),
                   'quarterly', 'cost_per_transaction_digital', 0, '')
    return csv


@app.route('/dashboard/<uuid>/cost-per-transaction/upload', methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def upload_cost_per_transaction(admin_client, uuid):

    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
        'data_group': admin_client.get_dashboard(uuid).get('slug'),
    })

    return render_template('builder/cost_per_transaction/upload.html',
                           uuid=uuid,
                           data_type=DATA_TYPE,
                           **template_context)


@app.route('/dashboard/<uuid>/cost-per-transaction/spreadsheet-template')
@requires_authentication
@requires_permission('dashboard')
def cost_per_transaction_spreadsheet_template(admin_client, uuid):
    csv = make_csv()
    response = make_response(csv)
    response.headers[
        "Content-Disposition"] = "attachment;filename=cost_per_transaction.csv"
    return response


@app.route('/dashboard/<uuid>/cost-per-transaction/upload', methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_cost_per_transaction_file(admin_client, uuid):

    # Create dashboard module and dataset.
    dashboard = admin_client.get_dashboard(uuid)
    owning_organisation = (
        dashboard.get('organisation', {})).get("name", 'Unknown')

    module_config = get_module_config_for_cost_per_transaction(
        owning_organisation)

    create_dataset_and_module(
        DATA_TYPE,
        admin_client,
        uuid,
        session.get('upload_choice', 'quarterly'),
        'single_timeseries',
        module_config,
        dashboard["slug"]
    )

    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    dashboard = admin_client.get_dashboard(uuid)
    data_group = dashboard["slug"]

    try:
        data_set = admin_client.get_data_set(data_group, DATA_TYPE)
    except HTTPError as err:
        return response(500, data_group, DATA_TYPE,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_cost_per_transaction_file', uuid=uuid))

    messages, status = upload_file_and_get_status(data_set)

    if messages:
        return response(status, data_group, DATA_TYPE, messages,
                        url_for('upload_cost_per_transaction',
                                uuid=uuid))

    return response(status, data_group, DATA_TYPE, messages,
                    url_for('upload_cost_per_transaction_success',
                            uuid=uuid))


@app.route('/dashboard/<uuid>/cost-per-transaction/upload/success',
           methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def upload_cost_per_transaction_success(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({'user': session['oauth_user']})
    dashboard = admin_client.get_dashboard(uuid)

    template_context.update(({
        'dashboard': {
            'title': dashboard["title"],
            'module': {
                'title': session['module']
            }
        },
        'admin_host': app.config['ADMIN_HOST'],
        'upload_period': 'quarterly'
    }))

    return render_template('builder/cost_per_transaction/upload-success.html',
                           uuid=uuid, **template_context)
