from flask import (
    render_template,
    session
)

from application import app

from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
    )


DASHBOARD_ROUTE = '/dashboard'


@app.route(
    '{0}/<uuid>/cost-per-transaction/upload'.format(DASHBOARD_ROUTE),
    methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def upload():
    print session


@app.route(
    '{0}/cost-per-transaction/confirmation'.format(DASHBOARD_ROUTE),
    methods=['GET'])
def cpt_confirmation():
    template_context = base_template_context()
    return render_template(
        'cost_per_transaction/confirmation.html',
        **template_context)