from admin import app
from admin.forms import DashboardCreationForm, ModuleTypes, DataSources
from admin.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
)
from flask import (
    flash, redirect, render_template, request,
    session, url_for
)
from admin.forms import convert_to_dashboard_form

import cgi
import json
import requests
import functools


DASHBOARD_ROUTE = '/administer-dashboards'


def update_modules_form_and_redirect(func):
    @functools.wraps(func)
    def wrapper(admin_client, uuid=None):

        def set_section_module_choices(modules):
            for m in [m for m in modules if m.category.data == 'container']:
                section_type = module_types.get_section_type()
                m.module_type.choices = [
                    (section_type['id'], section_type['name'])]
                m.module_type.data = section_type['id']
            return modules

        module_types = ModuleTypes(admin_client)
        data_sources = DataSources(
            admin_client, session['oauth_token']['access_token'])
        form = DashboardCreationForm(
            admin_client, module_types, data_sources, request.form)
        session['pending_dashboard'] = form.data
        if uuid is not None:
            session['pending_dashboard']['uuid'] = uuid

        if 'add_section' in request.form:
            url = url_for('dashboard_form',
                          uuid=uuid,
                          section=1,
                          modules=current_module_count(form) + 1)
            return redirect(url)

        if 'add_module' in request.form:
            url = url_for('dashboard_form',
                          uuid=uuid,
                          modules=current_module_count(form) + 1)
            return redirect(url)

        if move_or_remove(request.form, session):
            return redirect(url_for('dashboard_form', uuid=uuid))

        form.modules = set_section_module_choices(form.modules)

        if uuid is None:
            return func(admin_client, module_types, form)
        else:
            return func(admin_client, module_types, form, uuid)

    return wrapper


@app.route('{0}'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_index(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    dashboards_url = '{0}/dashboards'.format(app.config['STAGECRAFT_HOST'])
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


@app.route('{0}/new'.format(DASHBOARD_ROUTE), methods=['GET'])
@app.route('{0}/<uuid>'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_form(admin_client, uuid=None):
    def should_use_session(session, uuid):
        if 'pending_dashboard' not in session:
            return False
        if uuid is None:
            return True
        if session['pending_dashboard'].get('uuid') == uuid:
            return True
        return False

    def append_new_module_forms():
        total_modules = int(request.args.get('modules'))
        modules_required = total_modules - len(form.modules)
        for i in range(modules_required):
            form.modules.append_entry()
            choices = module_types.get_visualisation_choices()
            form.modules[-1].module_type.choices = choices
            choices = data_sources.group_choices()
            form.modules[-1].data_group.choices = choices
            choices = data_sources.type_choices()
            form.modules[-1].data_type.choices = choices

    template_context = base_template_context()
    template_context['user'] = session['oauth_user']
    if uuid is not None:
        template_context['uuid'] = uuid

    module_types = ModuleTypes(admin_client)
    data_sources = DataSources(
        admin_client, session['oauth_token']['access_token'])
    if should_use_session(session, uuid):
        form = DashboardCreationForm(admin_client,
                                     module_types,
                                     data_sources,
                                     data=session['pending_dashboard'])
    elif uuid is None:
        form = DashboardCreationForm(admin_client,
                                     module_types,
                                     data_sources,
                                     request.form)
    else:
        dashboard_dict = admin_client.get_dashboard(uuid)
        form = convert_to_dashboard_form(
            dashboard_dict, admin_client, module_types, data_sources)

    if 'pending_dashboard' in session:
        del session['pending_dashboard']

    if request.args.get('modules'):
        append_new_module_forms()
        if request.args.get('section'):
            form.modules[-1].category.data = 'container'

    return render_template('dashboards/create.html',
                           form=form,
                           **template_context)


@app.route('{0}/clone'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_clone(admin_client):
    template_context = base_template_context()
    template_context['user'] = session['oauth_user']
    dashboard_dict = admin_client.get_dashboard(request.args.get('uuid'))
    form = convert_to_dashboard_form(
        dashboard_dict,
        admin_client,
        ModuleTypes(admin_client),
        DataSources(admin_client, session['oauth_token']['access_token']))
    form['title'].data = ''
    form['slug'].data = ''
    form['published'].data = False
    for m in form.modules:
        m['id'].data = ''
    return render_template('dashboards/create.html',
                           form=form,
                           **template_context)


class InvalidFormFieldError(Exception):
    pass


@app.route('{0}/<uuid>'.format(DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
@update_modules_form_and_redirect
def dashboard_update(admin_client, module_types, form, uuid):
    try:
        if not form.validate():
            raise InvalidFormFieldError()
        dict_for_post = build_dict_for_post(form, module_types)
        admin_client.update_dashboard(uuid, dict_for_post)
        flash('Updated the <a href="{0}/performance/{1}">{2}</a> dashboard'
              .format(
                  app.config['GOVUK_SITE_URL'],
                  form.slug.data,
                  cgi.escape(form.title.data)
              ), 'success')
        del session['pending_dashboard']
        return redirect(url_for('dashboard_admin_index'))
    except (requests.HTTPError, ValueError, InvalidFormFieldError) as e:
        flash(format_error('updating', form, e), 'danger')
        return redirect(url_for('dashboard_form', uuid=uuid))


@app.route('{0}'.format(DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
@update_modules_form_and_redirect
def dashboard_create(admin_client, module_types, form):
    try:
        if not form.validate():
            raise InvalidFormFieldError()
        dict_for_post = build_dict_for_post(form, module_types)
        admin_client.create_dashboard(dict_for_post)
        flash('Created the {} dashboard'.format(form.slug.data), 'success')
        del session['pending_dashboard']
        return redirect(url_for('dashboard_admin_index'))
    except (requests.HTTPError, ValueError, InvalidFormFieldError) as e:
        flash(format_error('creating', form, e), 'danger')
        return redirect(url_for('dashboard_form'))


def create_or_udpate(admin_client, form):
    pass


def build_dict_for_post(form, module_types):
    def section_modules(modules):
        parent_module = None
        sectioned_modules = []
        for module in modules:
            if module['type_id'] == module_types.get_section_type()['id']:
                parent_module = module
                sectioned_modules.append(module)
            elif parent_module:
                parent_module['modules'].append(module)
            else:
                sectioned_modules.append(module)
        return sectioned_modules

    parsed_modules = []
    for (index, module) in enumerate(form.modules.entries, start=1):
        info = load_json_if_present(module.info.data.strip(), [])
        if not isinstance(info, list):
            raise ValueError("Info must be a list")
        for item in info:
            if not isinstance(item, basestring):
                raise ValueError("Info must all be strings")
        options = load_json_if_present(module.options.data.strip(), {})
        query_parameters = load_json_if_present(
            module.query_parameters.data.strip(), {})
        parsed_modules.append({
            # module.id ends up being the id of the subform, so we cant use the
            # magic method
            'id': module.data['id'],
            'type_id': module.module_type.data,
            'data_group': module.data_group.data,
            'data_type': module.data_type.data,
            'slug': module.slug.data,
            'title': module.title.data,
            'description': module.data['description'],
            'info': info,
            'options': options,
            'query_parameters': query_parameters,
            'order': index,
            'modules': [],
        })
    return {
        'published': form.published.data,
        'page-type': 'dashboard',
        'dashboard-type': form.dashboard_type.data,
        'slug': form.slug.data,
        'title': form.title.data,
        'description': form.description.data,
        'organisation': form.owning_organisation.data,
        'customer_type': form.customer_type.data,
        'business_model': form.business_model.data,
        'strapline': form.strapline.data,
        'costs': form.costs.data,
        'other_notes': form.other_notes.data,
        'links': [{
            'title': form.transaction_title.data,
            'url': form.transaction_link.data,
            'type': 'transaction',
        }],
        'modules': section_modules(parsed_modules),
    }


def format_error(verb, form, error):
    if isinstance(error, requests.HTTPError):
        return 'Error {} the {} dashboard: {}'.format(
            verb, form.slug.data, error.response.json()['message'])
    elif isinstance(error, InvalidFormFieldError):
        return 'Error {} the {} dashboard: {}'.format(
            verb, form.slug.data, to_error_list(form.errors))
    elif isinstance(error, ValueError):
        return 'Error validating the {} dashboard: {}'.format(
            form.slug.data, error.message)


def to_error_list(form_errors):
    def format_error(error):
        return '{0}: {1}'.format(field_name, error)

    messages = []
    for field_name, field_errors in form_errors.items():
        messages.append(','.join(map(format_error, field_errors)))
    return ', '.join(messages)


def load_json_if_present(data, default):
    if data:
        return json.loads(data)
    else:
        return default


def current_module_count(form):
    return len(form.modules)


def move_or_remove(request_form, session):
    """Move or remove a module and return True if a redirect is needed"""
    def get_module_index(field_prefix, form):
        for field in form.keys():
            if field.startswith(field_prefix):
                return int(field.replace(field_prefix, ''))

        return None

    # Remove a module from the list
    index = get_module_index('remove_module_', request.form)
    if index is not None:
        session['pending_dashboard']['modules'].pop(index)
        return True

    # Move a module down in the list (increment it's index number)
    index = get_module_index('move_module_down_', request.form)
    if index is not None:
        modules = session['pending_dashboard']['modules']
        if index < len(modules) - 1:
            modules[index], modules[
                index + 1] = modules[index + 1], modules[index]
            session['pending_dashboard']['modules'] = modules
        return True

    # Move a module up in the list (decrement it's index number)
    index = get_module_index('move_module_up_', request.form)
    if index is not None:
        modules = session['pending_dashboard']['modules']
        if index > 0:
            modules[index], modules[
                index - 1] = modules[index - 1], modules[index]
            session['pending_dashboard']['modules'] = modules
        return True
    return False
