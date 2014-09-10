from admin import app
from admin.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
)
from flask import render_template, session


@app.route('/administer-dashboards', methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_index(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    return render_template('dashboards/index.html', **template_context)
