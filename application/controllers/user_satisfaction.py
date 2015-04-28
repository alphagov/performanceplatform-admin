from application import app
from application.forms import DonePageURLForm
from flask import (
    session,
    render_template,
    redirect,
    url_for,
    flash
)
from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
    to_error_list,
    redirect_if_module_exists
)
import re

DASHBOARD_ROUTE = '/dashboard'


@app.route(
    '{0}/<uuid>/user-satisfaction/add'.format(DASHBOARD_ROUTE),
    methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
@redirect_if_module_exists('user-satisfaction-score')
def add_user_satisfaction(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    form = DonePageURLForm()
    if form.validate_on_submit():
        url = form.data['done_page_url']
        match = re.search('/done/([^/?]+)', url)
        if match is None:
            return redirect(url_for('get_in_touch', uuid=uuid))
        data_group = match.group(1)
        data_type = 'user-satisfaction-score'
        data_set = admin_client.get_data_set(data_group, data_type)
        if data_set is None:
            return redirect(url_for('get_in_touch', uuid=uuid))
        module_config = _module_config({
            'data_group': data_group,
            'data_type': data_type,
            'type_id': _get_user_satisfaction_module_type(admin_client)['id']})
        admin_client.add_module_to_dashboard(uuid, module_config)
        return redirect(url_for('dashboard_hub', uuid=uuid))
    if form.errors:
        flash(to_error_list(form.errors), 'danger')
    return render_template(
        'user_satisfaction/add.html',
        uuid=uuid,
        form=form,
        **template_context)


@app.route(
    '{0}/<uuid>/user-satisfaction/get-in-touch'.format(DASHBOARD_ROUTE))
@requires_authentication
@requires_permission('dashboard')
def get_in_touch(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })
    return render_template(
        'user_satisfaction/get-in-touch.html',
        email=app.config['NOTIFICATIONS_EMAIL'],
        uuid=uuid,
        **template_context)


def _module_config(options={}):
    module_config = {
        'slug': 'user-satisfaction',
        'title': 'User satisfaction',
        'description':
            'Average of scores rating satisfaction '
            'from 100% (very satisfied) to 0% (very dissatisfied)',
        'info': ['Data source: GOV.UK user feedback database',
                 "<a href='/service-manual/measurement/user-satisfaction' "
                 "rel='external'>User satisfaction</a> is measured by "
                 'surveying users at the point of transaction completion. '
                 'It is measured on a five-point scale, from most satisfied '
                 'to least satisfied. The mean of these responses is '
                 'converted to a percentage for display purposes.'],
        'options': {
            'axes': {
                'x': {'format': 'date',
                      'key': '_start_at',
                      'label': 'Date'},
                'y': [{'format': 'percent',
                       'key': 'score',
                       'label': 'User satisfaction'},
                      {'format': 'integer',
                       'key': 'rating_1',
                       'label': 'Very dissatisfied'},
                      {'format': 'integer',
                       'key': 'rating_2',
                       'label': 'Dissatisfied'},
                      {'format': 'integer',
                       'key': 'rating_3',
                       'label': 'Neither satisified or dissatisfied'},
                      {'format': 'integer',
                       'key': 'rating_4',
                       'label': 'Satisfied'},
                      {'format': 'integer',
                       'key': 'rating_5',
                       'label': 'Very satisfied'}]
            },
            'axis-period': 'month',
            'migrated': True,
            'total-attribute': 'num_responses',
            'trim': False,
            'value-attribute': 'score'
        },
        'query_parameters': {'sort_by': '_timestamp:ascending'},
        'order': 1
    }
    module_config.update(options)
    return module_config


def _get_user_satisfaction_module_type(admin_client):
    module_types = admin_client.list_module_types()
    for module_type in module_types:
        if module_type['name'] == 'user_satisfaction_graph':
            return module_type
