from admin import app
from flask import redirect, request, session, url_for, flash, abort
from requests_oauthlib import OAuth2Session
from requests import ConnectionError, Timeout
import logging


@app.route("/login", methods=['GET'])
def login():
    gds_session = OAuth2Session(app.config['SIGNON_OAUTH_ID'],
                                redirect_uri='{0}/auth/gds/callback'.format(
                                    app.config['ADMIN_HOST']))
    authorization_url, state = gds_session.authorization_url(
        '{0}/oauth/authorize'.format(app.config['SIGNON_BASE_URL']))
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route("/auth/gds/callback", methods=['GET'])
def authorize():
    gds_session = OAuth2Session(app.config['SIGNON_OAUTH_ID'],
                                state=session['oauth_state'],
                                redirect_uri='{0}/auth/gds/callback'.format(
                                    app.config['ADMIN_HOST']))
    token = gds_session.fetch_token('{0}/oauth/token'.format(
        app.config['SIGNON_BASE_URL']),
        client_secret=app.config['SIGNON_OAUTH_SECRET'],
        authorization_response=request.url)
    # need to pass ?client_id=[SIGNON_OAUTH_ID]
    user = gds_session.get('{0}/user.json'.format(
        app.config['SIGNON_BASE_URL'])).json()
    if 'signin' in user['user']['permissions']:
        session['oauth_user'] = user['user']
        session['oauth_token'] = token

        flash("You have been successfully signed in")
        session.store_session_for_user(user['user']['uid'])
    else:
        flash("You do not have access to this application.")

    return redirect(url_for('root'))


@app.route("/auth/gds/api/users/<uid>/reauth", methods=['POST'])
def reauth(uid):
    """ Force a user to reauth, triggered by sign-on-o-tron

    When a user signs out of sign-on-o-tron or is suspended, sign-on-o-tron
    will send an empty post request to the url of this controller, with a
    bearer token of the user that sends the request. The user which sends the
    request is specified by the sidekiq queue that sends the notifications from
    sign-on-o-tron. To ensure the request has come from sign-on-o-tron, we use
    this bearer token as an auth token and request the properties of the user -
    we only allow the request if the user has the user_update_permission.

    After authenticating the request, we delete all sessions for the user in
    redis, with the effect they will no longer be able to login to the admin
    app. Following gds-sso, we return a 200 if sucessful, despite this being a
    post request.

    Args:
        uid: a sign-on-o-tron user_id

    Returns:
        200 on success
        403 on failure, as the user didnt have the correct permissions.
    """
    invalid_message = 'Invalid Authorization header supplied'
    token = validate_bearer_token(request.headers, invalid_message)
    gds_session = OAuth2Session(
        app.config['SIGNON_OAUTH_ID'],
        token={'access_token': token, 'type': 'Bearer'},
    )
    try:
        user_request = gds_session.get('{0}/user.json'.format(
            app.config['SIGNON_BASE_URL']), timeout=30)
    except (Timeout, ConnectionError):
        abort(500, 'Error connecting to signon service')
    if str(user_request.status_code)[0] in ('4', '5'):
        abort(user_request.status_code, user_request.reason)
    try:
        user = user_request.json()
    except ValueError:
        abort(500, 'Unable to parse signon json')

    if 'user_update_permission' in user['user']['permissions']:
        session.delete_sessions_for_user(uid)
        return ''
    abort(403)


def validate_bearer_token(headers, invalid_message=''):
    try:
        bearer = headers['Authorization']
    except KeyError:
        abort(403, 'No Authorization header supplied')
    bearer_parts = bearer.split()
    if bearer_parts[0] != 'Bearer':
        abort(403, invalid_message)
    if len(bearer_parts) != 2:
        abort(403, invalid_message)
    token = bearer_parts[1]
    return token
