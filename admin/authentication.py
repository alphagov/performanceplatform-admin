from admin import app
from flask import redirect, request, session, url_for, flash
from requests_oauthlib import OAuth2Session


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
    else:
        flash("You do not have access to this application.")

    return redirect(url_for('root'))
