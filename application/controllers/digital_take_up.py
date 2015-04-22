from requests import HTTPError
from application import app
from application.controllers.upload import response, upload_file_and_get_status
from application.forms import UploadOptionsForm, ChannelOptionsForm
from flask import (
    session,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    make_response
)
from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
    to_error_list,
    generate_bearer_token)
from application.utils.datetimeutil import (
    a_week_ago,
    a_month_ago,
    start_of_week,
    start_of_month,
    to_datetime
)

DASHBOARD_ROUTE = '/dashboard'


@app.route(
    '{0}/<uuid>/digital-take-up/upload-options'.format(DASHBOARD_ROUTE),
    methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_options(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    form = UploadOptionsForm()
    if form.validate_on_submit():
        session['upload_choice'] = form.data['upload_option']
        if session['upload_choice'] != 'api':
            return redirect(url_for('channel_options', uuid=uuid))
        else:
            return redirect(url_for('api_get_in_touch', uuid=uuid))
    if form.errors:
        flash(to_error_list(form.errors), 'danger')
    return render_template(
        'digital_take_up/upload-options.html',
        uuid=uuid,
        upload_options=[option for option in form.upload_option],
        form=form,
        **template_context)


@app.route(
    '{0}/<uuid>/digital-take-up/api-get-in-touch'.format(DASHBOARD_ROUTE))
@requires_authentication
@requires_permission('dashboard')
def api_get_in_touch(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })
    return render_template(
        'digital_take_up/api-get-in-touch.html',
        email=app.config['NOTIFICATIONS_EMAIL'],
        uuid=uuid,
        **template_context)


def get_or_create_data_set_transform(
        admin_client, uuid, transform_config, data_set):

    try:
        transform = admin_client.get_data_set_transforms(data_set["name"])
    except HTTPError as err:
        return response(500, transform_config, data_set,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_digital_take_up_data_file',
                                uuid=uuid))

    if not transform:
        transform = admin_client.create_transform(transform_config)

    return transform


def get_transform_config_for_digital_takeup(data_group, period):
    transform_config = {
        "type_id": "8e8d973b-3937-430d-944f-56bbeee13af2",
        "input": {
            "data-type": "transactions-by-channel",
            "data-group": data_group
        },
        "query-parameters": {
            "collect": ["count:sum"],
            "group_by": "channel",
            "period": period
        },
        "options": {
            "denominatorMatcher": ".+",
            "numeratorMatcher": "^digital$",
            "matchingAttribute": "channel",
            "valueAttribute": "count:sum"
        },
        "output": {
            "data-type": "digital-takeup",
            "data-group": data_group
        }
    }

    return transform_config


@app.route(
    '{0}/<uuid>/digital-take-up/channel-options'.format(DASHBOARD_ROUTE),
    methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def channel_options(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    form = ChannelOptionsForm()
    if request.method == 'POST':
        if True in form.data.values():
            session['channel_choices'] = [
                key for key, val in form.data.items() if val]

            dashboard = admin_client.get_dashboard(uuid)
            owning_organisation = (dashboard.get('organisation') or {}).get(
                "name", 'Unknown')

            module_config = get_module_config_for_digital_takeup(
                owning_organisation)

            create_dataset_and_module(
                'transactions-by-channel',
                admin_client,
                uuid,
                session['upload_choice'],
                'single_timeseries',
                module_config,
                dashboard["slug"],
                'digital-takeup'
            )

            return redirect(url_for('upload_digital_take_up_data_file',
                                    uuid=uuid))
        else:
            error = 'Please select one or more channel options.'
            flash(error, 'danger')
    return render_template(
        'digital_take_up/channel-options.html',
        uuid=uuid,
        form=form,
        **template_context)


@app.route(
    '{0}/<uuid>/digital-take-up/spreadsheet-template'.format(DASHBOARD_ROUTE))
@requires_authentication
@requires_permission('dashboard')
def spreadsheet_template(admin_client, uuid):
    csv = make_csv()
    response = make_response(csv)
    response.headers[
        "Content-Disposition"] = "attachment; filename=digital_take_up.csv"
    return response


def make_csv():
    csv = "_timestamp,period,channel,count\n"
    if session['upload_choice'] == 'week':
        start_date = start_of_week(a_week_ago())
    else:
        start_date = start_of_month(a_month_ago())
    timestamp = to_datetime(start_date).isoformat()
    for channel in session['channel_choices']:
        csv += '{0},{1},{2},0\n'.format(
            timestamp,
            session['upload_choice'],
            channel)
    return csv


def create_dataset_and_module(input_data_type,
                              admin_client,
                              uuid,
                              period,
                              module_type,
                              module_config,
                              data_group_name,
                              output_data_type=None):

    # DATA GROUP
    data_group = get_or_create_data_group(
        admin_client, data_group_name, input_data_type, uuid)

    # DATA SET
    input_data_set = get_or_create_data_set(
        admin_client, uuid, data_group['name'], input_data_type, period)

    if output_data_type:
        output_data_set = get_or_create_data_set(
            admin_client, uuid, data_group['name'], output_data_type, period)

        transform_config = get_transform_config_for_digital_takeup(
            data_group_name, session["upload_choice"])

        transform = get_or_create_data_set_transform(admin_client,
                                                     uuid,
                                                     transform_config,
                                                     input_data_set)
        input_data_type = output_data_type

    # MODULE
    module = create_module_if_not_exists(
        admin_client,
        data_group['name'],
        input_data_type,
        module_config,
        module_type)

    session['module'] = module_config['title']


def get_module_config_for_digital_takeup(owning_organisation):
    module_config = {
        "slug": "digital-takeup",
        "title": "Digital take-up",
        "description": "What percentage of transactions were completed "
                       "using the online service",
        "info": ["Data source: {}".format(owning_organisation),
                 "<a href='/service-manual/measurement/digital-takeup' "
                 "rel='external'>Digital take-up</a> measures the "
                 "percentage of completed applications that are made "
                 "through a digital channel versus non-digital channels."],
        "options": {
            "axes": {
                "x": {
                    "format": "date",
                    "key": [
                        "_start_at",
                        "_end_at"
                    ],
                    "label": "Date"
                },
                "y": [
                    {
                        "label": "Completion percentage"
                    }
                ]
            },
            "format-options": {
                "type": "percent"
            },
            "value-attribute": "rate"
        },
        "query_parameters": {
            "sort_by": "_timestamp:ascending"
        },
        "order": 2
    }
    return module_config


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
            module_config["type_id"] = module_type['id']

    try:
        module = admin_client.add_module_to_dashboard(
            data_group, module_config)
        return module
    except HTTPError as e:
        exists = "Module with this Dashboard and Slug already exists"
        if exists not in e.response.text:
            raise


def get_or_create_data_set(admin_client, uuid, data_group, data_type,
                           period):

    data_set_config = get_data_set_config(data_group, data_type,
                                          period)

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


def get_data_set_config(data_group_name, data_type, period):
    if period == 'week':
        max_age_expected = 1300000
    else:
        max_age_expected = 5200000

    data_set_config = {
        'data_type': data_type,
        'data_group': data_group_name,
        'bearer_token': generate_bearer_token(),
        'upload_format': 'csv',
        'max_age_expected': max_age_expected
    }
    return data_set_config


def get_or_create_data_group(admin_client, data_group_name, data_type, uuid):
    data_group_config = {"name": data_group_name}

    try:
        data_group = admin_client.get_data_group(data_group_name)
    except HTTPError as err:
        return response(500, data_group_config, data_type,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_digital_take_up_data_file',
                                uuid=uuid))
    if not data_group:
        data_group = admin_client.create_data_group(data_group_config)

    return data_group


@app.route('/dashboard/<uuid>/digital-take-up/upload',
           methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def upload_digital_take_up_data_file(admin_client, uuid):
    DATA_TYPE_NAME = 'transactions-by-channel'
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    if 'upload_data' in session:
        upload_data = session.pop('upload_data')
        template_context['upload_data'] = upload_data

    return render_template('digital_take_up/upload.html',
                           uuid=uuid,
                           data_type=DATA_TYPE_NAME,
                           **template_context)


@app.route('/dashboard/<uuid>/digital-take-up/upload',
           methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_data_file_to_dashboard(admin_client, uuid):
    DATA_TYPE_NAME = 'transactions-by-channel'
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    dashboard = admin_client.get_dashboard(uuid)
    data_group = dashboard["slug"]

    try:
        data_set = admin_client.get_data_set(data_group, DATA_TYPE_NAME)
    except HTTPError as err:
        return response(500, data_group, DATA_TYPE_NAME,
                        ['[{}] {}'.format(err.response.status_code,
                                          err.response.json())],
                        url_for('upload_data_file_to_dashboard', uuid=uuid))

    messages, status = upload_file_and_get_status(data_set)

    if messages:
        return response(status, data_group, DATA_TYPE_NAME, messages,
                        url_for('upload_digital_take_up_data_file',
                                uuid=uuid))

    return response(status, data_group, DATA_TYPE_NAME, messages,
                    url_for('upload_digital_take_up_data_success',
                            uuid=uuid))


@app.route('/dashboard/<uuid>/digital-take-up/upload/success',
           methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_digital_take_up_data_success(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    dashboard = admin_client.get_dashboard(uuid)

    template_context.update(({
        'dashboard': {
            'title': dashboard["title"],
            'module': {
                'title': session['module']
            }
        },
        'admin_host': app.config['ADMIN_HOST'],
        'upload_period': session['upload_choice']
    }))

    return render_template('digital_take_up/upload_success.html',
                           uuid=uuid,
                           **template_context)
