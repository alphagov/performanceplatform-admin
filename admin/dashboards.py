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

    if request.args.get('modules'):
        total_modules = int(request.args.get('modules'))
        modules_required = total_modules - len(form.modules)
        for i in range(modules_required):
            form.modules.append_entry()

    return render_template('dashboards/create.html',
                           form=form,
                           **template_context)


@app.route('{0}/create'.format(DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_create_post(admin_client):
    def get_module_index(field_prefix, form):
        for field in form.keys():
            if field.startswith(field_prefix):
                return int(field.replace(field_prefix, ''))

        return None

    form = DashboardCreationForm(request.form)
    session['pending_dashboard'] = form.data

    # Add a new empty module
    if 'add_module' in request.form:
        current_modules = len(
            DashboardCreationForm(
                data=session['pending_dashboard']).modules)
        return redirect(url_for('dashboard_admin_create',
                                modules=current_modules+1))

    # Remove a module from the list
    index = get_module_index('remove_module_', request.form)
    if index is not None:
        session['pending_dashboard']['modules'].pop(index)
        return redirect(url_for('dashboard_admin_create'))

    # Move a module down in the list (increment it's index number)
    index = get_module_index('move_module_down_', request.form)
    if index is not None:
        modules = session['pending_dashboard']['modules']
        if index < len(modules) - 1:
            modules[index], modules[index+1] = modules[index+1], modules[index]
            session['pending_dashboard']['modules'] = modules
        return redirect(url_for('dashboard_admin_create'))

    # Move a module up in the list (decrement it's index number)
    index = get_module_index('move_module_up_', request.form)
    if index is not None:
        modules = session['pending_dashboard']['modules']
        if index > 0:
            modules[index], modules[index-1] = modules[index-1], modules[index]
            session['pending_dashboard']['modules'] = modules
        return redirect(url_for('dashboard_admin_create'))

    parsed_modules = []

    for (index, module) in enumerate(form.modules.entries, start=1):
        parsed_modules.append({
            'type_id': module.module_type.data,
            'data_group': module.data_group.data,
            'data_type': module.data_type.data,
            'slug': module.slug.data,
            'title': module.title.data,
            'description': module.module_description.data,
            'info': module.info.data.split("\n"),
            'options': json.loads(module.options.data),
            'query_parameters': json.loads(module.query_parameters.data),
            'order': index,
        })

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
        }],
        'modules': parsed_modules,
    }

    try:
        admin_client.create_dashboard(data)
        if 'pending_dashboard' in session:
            del session['pending_dashboard']
        flash('Created the {} dashboard'.format(form.slug.data), 'success')
        return redirect(url_for('dashboard_admin_index'))
    except requests.HTTPError as e:
        formatted_error = 'Error creating the {} dashboard: {}'.format(
            form.slug.data, e.response.json()['message'])
        flash(formatted_error, 'danger')
        return redirect(url_for('dashboard_admin_create'))
