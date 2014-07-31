from admin import app
from flask import session, redirect, url_for
from functools import wraps
from os import getenv
from performanceplatform.client.admin import AdminAPI


GOVUK_ENV = getenv('GOVUK_ENV', 'development')


def get_context(session_object):
    context = dict()

    if 'oauth_user' in session_object and 'oauth_token' in session_object:
        admin_client = AdminAPI(app.config['STAGECRAFT_HOST'],
                                session_object['oauth_token']['access_token'])
        context = {
            'user': session_object['oauth_user'],
            'data_sets': admin_client.list_data_sets()
        }

    context['environment'] = environment_dict()

    return context


def environment_dict():
    return {
        'name': GOVUK_ENV,
        'human_name': GOVUK_ENV[:1].upper() + GOVUK_ENV[1:]
    }


def requires_authentication(func):
    @wraps(func)
    def verify_user_logged_in(*args, **kwargs):
        session_context = get_context(session)
        print session_context
        if 'user' not in session_context:
            print "REDIRECTING, UNAUTHORISED"
            return redirect(url_for('root'))
        kwargs['session_context'] = session_context
        return func(*args, **kwargs)
    return verify_user_logged_in
