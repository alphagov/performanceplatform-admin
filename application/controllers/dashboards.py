from collections import namedtuple
from application.forms import DashboardHubForm
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session
)
from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
    to_error_list
)
from application import app

import requests


DASHBOARD_ROUTE = '/dashboards'


@app.route('{0}/<uuid>'.format(DASHBOARD_ROUTE), methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_hub(admin_client, uuid):
    template_context = base_template_context()
    dashboard_dict = admin_client.get_dashboard(uuid)
    Dashboard = namedtuple('Dashboard', dashboard_dict.keys())
    dashboard = Dashboard(**dashboard_dict)
    form = DashboardHubForm(obj=dashboard)
    if form.validate_on_submit():
        admin_client.update_dashboard(uuid, form.data)
        return redirect(url_for('dashboard_admin_index'))
    if form.errors:
        flash(to_error_list(form.errors), 'danger')
    preview_url = "{0}/performance/{1}".format(
        app.config['GOVUK_SITE_URL'], dashboard_dict['slug'])
    return render_template(
        'dashboards/dashboard-hub.html',
        uuid=uuid,
        dashboard_title=dashboard.title,
        preview_url=preview_url,
        form=form,
        **template_context)


@app.route('/dashboards', methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_list(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    dashboards_url = '{0}/dashboards'.format(
        app.config['STAGECRAFT_HOST'])
    access_token = session['oauth_token']['access_token']
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }

    dashboard_response = requests.get(dashboards_url, headers=headers)

    if dashboard_response.status_code == 200:
        dashboards = dashboard_response.json()['dashboards']
        if len(dashboards) == 0:
            flash('No dashboards stored', 'info')
    else:
        flash('Could not retrieve the list of dashboards', 'danger')
        dashboards = None

    return render_template('dashboards/index.html',
                           dashboards=dashboards,
                           **template_context)
