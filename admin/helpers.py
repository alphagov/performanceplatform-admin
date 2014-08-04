from admin import app
from flask import session, redirect, url_for
from functools import wraps
from os import getenv
from performanceplatform.client.admin import AdminAPI


GOVUK_ENV = getenv('GOVUK_ENV', 'development')


def requires_authentication(f):
    @wraps(f)
    def verify_user_logged_in(*args, **kwargs):
        if not signed_in(session):
            return redirect(url_for('root'))
        else:
            admin_client = get_admin_client(session)
            kwargs['admin_client'] = admin_client
            return f(*args, **kwargs)
    return verify_user_logged_in


def get_admin_client(session):
    return AdminAPI(app.config['STAGECRAFT_HOST'],
                    session['oauth_token']['access_token'])


def base_template_context():
    return {
        'environment': {
            'name': GOVUK_ENV,
            'human_name': GOVUK_ENV[:1].upper() + GOVUK_ENV[1:]
        }
    }


def signed_in(session):
    return 'oauth_user' in session and 'oauth_token' in session
