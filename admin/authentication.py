from admin import app
from flask import jsonify, redirect, request, session, url_for
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
    user = gds_session.get('{0}/user.json'.format(
        app.config['SIGNON_BASE_URL'])).json()
    session['user'] = {
        'name': user['user']['name'],
        'email': user['user']['email'],
        'permissions': user['user']['permissions'],
    }
    return redirect(url_for('root'))
