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

from oauth2client import client

import httplib2
from apiclient.discovery import build

import json

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
            methods=['GET'])
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

@app.route('/dashboard/<uuid>/completion-rate/auth',
            methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def auth(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    flow = client.flow_from_clientsecrets(
        'top-secret-do-not-commit.json',
        scope='https://www.googleapis.com/auth/analytics.readonly',
        redirect_uri='http://admin.development.performance.service.gov.uk/dashboard/completion-rate/auth-callback')

    auth_uri = flow.step1_get_authorize_url()
    redirect_uri = "{0}&state={1}".format(auth_uri, uuid)

    return redirect(redirect_uri)

@app.route('/dashboard/completion-rate/auth-callback',
            methods=['GET'])
@requires_authentication
@requires_feature('edit-dashboards')
def auth_callback(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    flow = client.flow_from_clientsecrets(
        'top-secret-do-not-commit.json',
        scope='https://www.googleapis.com/auth/analytics.readonly',
        redirect_uri='http://admin.development.performance.service.gov.uk/dashboard/completion-rate/auth-callback')


    credentials = flow.step2_exchange(request.args['code'])
    http_auth = credentials.authorize(httplib2.Http())
    session['credentials']=credentials
    return redirect(url_for('choose_ga_profile_and_goal', uuid=request.args['state']));


@app.route('/dashboard/<uuid>/completion-rate/choose-ga-profile-and-goal',
            methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def choose_ga_profile_and_goal(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    if request.method == 'POST':
        return redirect(url_for('confirm_data_choices', uuid=uuid))

    http_auth = session['credentials'].authorize(httplib2.Http())

    analytics_service = build('analytics', 'v3', http=http_auth)

    analytics_request = analytics_service.management().profiles().list(accountId='~all', webPropertyId='~all')
    response = analytics_request.execute()

    goals = {}
    profiles = response['items']
    for profile in profiles:
        profile_request = analytics_service.management().goals().list(profileId=profile['id'], webPropertyId=profile['webPropertyId'], accountId=profile['accountId'])
        response = profile_request.execute()
        goals[profile['id']] = response['items']

    # put them on the page
    return render_template('builder/completion-rate/choose-ga-profile-and-goal.html',
                           uuid=uuid,
                           data_type=DATA_TYPE,
                           profiles=profiles,
                           goals=goals,
                           **template_context)

@app.route('/dashboard/<uuid>/completion-rate/check-data',
            methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def check_data(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    
