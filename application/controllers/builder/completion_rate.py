import json

from flask import (
    session,
    render_template,
    url_for,
    request,
    redirect
)

from application import app
from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_feature
)

from oauth2client import client

import httplib2
from apiclient.discovery import build

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


def get_ga_redirect():
    with open('top-secret-do-not-commit.json') as ga_redirect:
        ga_redirect_uri = json.load(ga_redirect)

    ga_uri = ga_redirect_uri["web"]["redirect_uris"][0]
    return ga_uri


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
        redirect_uri=get_ga_redirect())

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
        redirect_uri=get_ga_redirect())

    credentials = flow.step2_exchange(request.args['code'])
    #http_auth = credentials.authorize(httplib2.Http())
    session['credentials'] = credentials
    return redirect(url_for('choose_ga_profile_and_goal', uuid=request.args['state']))


@app.route('/dashboard/<uuid>/completion-rate/choose-ga-profile-and-goal',
           methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def choose_ga_profile_and_goal(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    http_auth = session['credentials'].authorize(httplib2.Http())
    analytics_service = build('analytics', 'v3', http=http_auth)
    analytics_request = analytics_service.management().profiles().list(accountId='~all',
                                                                       webPropertyId='~all')
    profile_list = analytics_request.execute()

    if request.method == 'POST':
        chosen_profile = {}
        chosen_id = request.form.get('profile_id')

        for profile in profile_list['items']:
            if profile['id'] == chosen_id:
                chosen_profile = profile
                break

        return redirect(url_for('check_data', uuid=uuid,
                                profileId=chosen_profile['id'],
                                webPropertyId=chosen_profile['webPropertyId'],
                                accountId=chosen_profile['accountId'],
                                goalId=request.form.get('goal')))

    goals = {}
    profiles = profile_list['items']
    for profile in profiles:
        profile_request = analytics_service.management().goals().list(profileId=profile['id'],
                                                                      webPropertyId=profile['webPropertyId'],
                                                                      accountId=profile['accountId'])
        response = profile_request.execute()
        goals[profile['id']] = response['items']

    # put them on the page
    return render_template('builder/completion-rate/choose-ga-profile-and-goal.html',
                           uuid=uuid,
                           data_type=DATA_TYPE,
                           profiles=profiles,
                           goals=goals,
                           **template_context)


#check-data?profileId=id&webPropertyId=webPropertyId&goalId=goalId&accountId=accountId
@app.route('/dashboard/<uuid>/completion-rate/check-data',
           methods=['GET', 'POST'])
@requires_authentication
@requires_feature('edit-dashboards')
def check_data(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })

    http_auth = session['credentials'].authorize(httplib2.Http())
    analytics_service = build('analytics', 'v3', http=http_auth)
    goal_request = analytics_service.management().goals().get(
        accountId=request.args.get('accountId', ''),
        webPropertyId=request.args.get('webPropertyId', ''),
        goalId=request.args.get('goalId', ''),
        profileId=request.args.get('profileId', ''))
    response = goal_request.execute()

    goal_name = response['name']
    goal_info = response['urlDestinationDetails']
    destination_url = goal_info['url']

    ga_completion_request = analytics_service.data().ga().get(
        ids='ga:' + request.args.get('profileId', ''),
        start_date='7daysAgo',
        end_date='today',
        metrics='ga:goal' + request.args.get('goalId', '') + 'Completions')
    ga_completion_response = ga_completion_request.execute()
    conversions = ga_completion_response['rows'][0][0]

    return render_template('builder/completion-rate/check-data.html',
                           uuid=uuid,
                           data_type=DATA_TYPE,
                           destination_url=destination_url,
                           conversions=conversions,
                           goal_name=goal_name,
                           **template_context)
