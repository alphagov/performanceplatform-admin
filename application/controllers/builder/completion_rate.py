from requests import HTTPError

from flask import (
    flash,
    session,
    render_template,
    make_response,
    url_for,
    request,
    redirect
)

from application import app
from application.controllers.upload import (
    response
)
from application.helpers import (
    base_template_context,
    generate_bearer_token,
    requires_authentication,
    requires_feature
)
from application.utils.datetimeutil import (
    previous_year_quarters,
    end_of_quarter
)
from application.controllers.builder.common import(
    upload_data_and_respond)

DATA_TYPE = 'completion-rate'

@app.route('/dashboard/<uuid>/completion-rate/choose-a-provider',
            methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def choose_a_provider(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    '''
    Not going to store any of this, let's just say they always choose Google
    Analytics
    '''
    if request.method == 'POST':
        return redirect(url_for('set_up_provider', uuid=uuid))

    return render_template('builder/completion-rate/choose-a-provider.html',
                           uuid=uuid,
                           data_type=DATA_TYPE,
                           **template_context)

@app.route('/dashboard/<uuid>/completion-rate/set-up-provider',
            methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def set_up_provider(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    return render_template('builder/completion-rate/set-up-provider.html',
                           uuid=uuid,
                           data_type=DATA_TYPE,
                           **template_context)
