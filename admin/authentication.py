from admin import app
from flask import redirect, request, session, url_for, flash
from requests_oauthlib import OAuth2Session


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
