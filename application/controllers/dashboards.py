from collections import namedtuple
from application.forms import DashboardHubForm
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session
)
import boto.ses
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
    template_context.update({
        'user': session['oauth_user'],
    })
    dashboard_dict = admin_client.get_dashboard(uuid)
    if dashboard_dict['status'] != 'unpublished':
        flash('In review or published dashboards cannot be edited', 'info')
        return redirect(url_for('dashboard_list'))

    Dashboard = namedtuple('Dashboard', dashboard_dict.keys())
    dashboard = Dashboard(**dashboard_dict)
    modules = []
    if "modules" in dashboard_dict.keys():
        modules = [module["data_type"] for module in dashboard_dict["modules"]]
    form = DashboardHubForm(obj=dashboard)
    if form.validate_on_submit():
        admin_client.update_dashboard(uuid, form.data)
        return redirect(url_for('dashboard_list'))
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
        modules=modules,
        **template_context)


@app.route('{0}/<uuid>/send-for-review'.format(
    DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def send_dashboard_for_review(admin_client, uuid):
    dashboard_dict = admin_client.get_dashboard(uuid)
    admin_client.update_dashboard(uuid, {'status': 'in-review'})

    conn = boto.ses.connect_to_region(
        'us-east-1',
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])

    body_text = "{0} ({1}) requests a review of the dashboard ({2})".format(
        session['oauth_user']['name'],
        session['oauth_user']['email'],
        dashboard_dict['title'])

    conn.send_email(
        app.config['NO_REPLY_EMAIL'],
        'Request to review a dashboard',
        body_text,
        app.config['NOTIFICATIONS_EMAIL'],
        reply_addresses=app.config['NO_REPLY_EMAIL'])

    flash('Your dashboard has been sent for review', 'success')
    return redirect(url_for('dashboard_list'))


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
