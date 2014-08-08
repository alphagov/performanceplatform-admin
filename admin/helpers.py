from admin import app
from flask import session, redirect, url_for
from functools import wraps
from os import getenv
from performanceplatform.client.admin import AdminAPI
from itertools import groupby
from operator import itemgetter


environment = getenv('INFRASTRUCTURE_ENV', 'development')


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
            'name': environment,
            'human_name': environment.capitalize()
        }
    }


def signed_in(session):
    return 'oauth_user' in session and 'oauth_token' in session


def group_by_group(data_sets):
    grouped_data_sets = {}
    for item in data_sets:
        if item['data_group'] in grouped_data_sets:
            grouped_data_sets[item['data_group']].append(item)
        else:
            grouped_data_sets[item['data_group']] = []
            grouped_data_sets[item['data_group']].append(item)
    return grouped_data_sets
