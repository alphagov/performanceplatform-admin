from application import app, csrf
from flask import redirect, request, session, url_for, flash
from requests_oauthlib import OAuth2Session
from application.helpers import api_permission_required, get_admin_client


def get_authorization_url(session):
    gds_session = OAuth2Session(app.config['SIGNON_OAUTH_ID'],
                                redirect_uri='{0}/auth/gds/callback'.format(
                                    app.config['ADMIN_HOST']))
    authorization_url, state = gds_session.authorization_url(
        '{0}/oauth/authorize'.format(app.config['SIGNON_BASE_URL']))
    session['oauth_state'] = state
    return authorization_url


@app.route("/sign-out")
def oauth_sign_out():
    session.clear()
    return redirect(app.config['SIGNON_BASE_URL'] + '/users/sign_out')


if app.config['DEBUG']:
    @app.route("/sign-in")
    def fake_oath_sign_in():
        session['oauth_user'] = app.config['FAKE_OAUTH_USER']
        session['oauth_token'] = {
            'access_token': app.config['FAKE_OAUTH_TOKEN']
        }

        return redirect(url_for('root'))


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
    user = gds_session.get('{0}/user.json?client_id={1}'.format(
        app.config['SIGNON_BASE_URL'],
        app.config['SIGNON_OAUTH_ID'])).json()
    if 'signin' in user['user']['permissions']:
        flash("You have been successfully signed in")
    session['oauth_user'] = user['user']
    session['oauth_token'] = token

    return redirect(url_for('root'))


@app.route("/auth/gds/api/users/<uid>", methods=['PUT'])
@csrf.exempt
@api_permission_required('user_update_permission')
def update(uid):
    """Update a user, triggered by sign-on-o-tron

    When a user is updated in sign-on-o-tron, sign-on-o-tron
    will send a PUT request to the url of this controller, with a
    bearer token of the user that sends the request. The user which sends the
    request is specified by the sidekiq queue that sends the notifications from
    sign-on-o-tron. To ensure the request has come from sign-on-o-tron, we use
    this bearer token as an auth token and request the properties of the user -
    we only allow the request if the user has the user_update_permission.

    After authenticating the request, we read the JSON request body and update
    the stored representation of the user in our app, if present.

    Following the model in gds-sso, we return a 200 if succesful.

    Args:
        uid: a sign-on-o-tron user_id

    Returns:
        200 on success
    """
    # For now, we implement this as a no-op
    return ''


@app.route("/auth/gds/api/users/<uid>/reauth", methods=['POST'])
@csrf.exempt
@api_permission_required('user_update_permission')
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
        403 on failure, as the user didn't have the correct permissions.
    """
    session.delete_sessions_for_user(uid)
    get_admin_client(session).reauth(uid)
    return ''
