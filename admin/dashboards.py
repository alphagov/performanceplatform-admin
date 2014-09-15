from admin import app
from admin.forms import DashboardCreationForm
from admin.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
)
from flask import (
    flash, redirect, render_template, request,
    session, url_for
)

import json
import requests


DASHBOARD_ROUTE = '/administer-dashboards'


@app.route('{0}'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_index(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    return render_template('dashboards/index.html', **template_context)


@app.route('{0}/create'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_create(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    if 'pending_dashboard' in session:
        form = DashboardCreationForm(data=session['pending_dashboard'])
    else:
        form = DashboardCreationForm(request.form)

    return render_template('dashboards/create.html',
                           form=form,
                           **template_context)


@app.route('{0}/create'.format(DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_create_post(admin_client):
    form = DashboardCreationForm(request.form)

    access_token = session['oauth_token']['access_token']
    dashboard_url = "{0}/dashboard".format(app.config['STAGECRAFT_HOST'])
    data = {
        'published': False,
        'page-type': 'dashboard',
        'dashboard-type': form.dashboard_type.data,
        'slug': form.slug.data,
        'title': form.title.data,
        'description': form.description.data,
        'customer_type': form.customer_type.data,
        'business_model': form.business_model.data,
        'strapline': form.strapline.data,
        'links': [{
            'title': form.transaction_title.data,
            'url': form.transaction_link.data,
            'type': 'transaction',
        }]
    }
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'Content-type': 'application/json',
    }

    create_dashboard = requests.post(dashboard_url,
                                     data=json.dumps(data),
                                     headers=headers)

    if create_dashboard.status_code == 200:
        if 'pending_dashboard' in session:
            del session['pending_dashboard']
        flash('Created the {0} dashboard'.format(form.slug.data), 'success')
        return redirect(url_for('dashboard_admin_index'))
    else:
        session['pending_dashboard'] = request.form
        stagecraft_message = create_dashboard.json()['message']
        formatted_error = 'Error creating the {0} dashboard: {1}'.format(
            form.slug.data, stagecraft_message)
        flash(formatted_error, 'danger')
        return redirect(url_for('dashboard_admin_create'))
