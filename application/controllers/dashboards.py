from application import app
from collections import namedtuple
from application.forms import DashboardHubForm
from flask import (
    render_template,
    redirect,
    url_for,
    flash
)
from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
    to_error_list
)


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
