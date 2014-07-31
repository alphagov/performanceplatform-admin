from admin import app
from admin.helpers import requires_authentication, base_template_context
from flask import render_template, session, redirect, url_for
import requests


@app.route('/upload-data', methods=['GET'])
@requires_authentication
def upload_list_data_sets(admin_client):
    template_context = base_template_context()
    try:
        data_sets = admin_client.list_data_sets()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 403:
            return redirect(url_for('oauth_sign_out'))
        else:
            raise
    template_context.update({
        'user': session['oauth_user'],
        'data_sets': data_sets
    })
    return render_template('data_sets.html', **template_context)
