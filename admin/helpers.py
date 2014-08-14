from admin import app
from flask import session, redirect, url_for
from functools import wraps
from os import getenv
from performanceplatform.client.admin import AdminAPI


environment = getenv('INFRASTRUCTURE_ENV', 'development')


@app.context_processor
def view_helpers():
    def can_edit_dashboards(user):
        return 'permissions' in user and \
            'dashboard-editor' in user['permissions']

    return dict(can_edit_dashboards=can_edit_dashboards)


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


def requires_permission(permission=None):
    def wrap(f):

        @wraps(f)
        def verify_user_has_permission(*args, **kwargs):
            if permission is None:
                raise Exception('@requires_permission needs an argument')

            if not signed_in(session):
                return redirect(url_for('root'))

            user_permissions = session['oauth_user']['permissions']

            if permission in user_permissions:
                return f(*args, **kwargs)
            else:
                return redirect(url_for('root'))

        return verify_user_has_permission

    return wrap


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
    return(has_user_with_token(session)
           and not no_access(session['oauth_user']))


def signed_in_no_access(session):
    return(has_user_with_token(session)
           and no_access(session['oauth_user']))


def has_user_with_token(session):
    return('oauth_token' in session
           and 'access_token' in session['oauth_token']
           and 'oauth_user' in session)


def no_access(session_oauth_user):
    return('permissions' not in session_oauth_user
           or 'signin' not in session_oauth_user['permissions'])


def group_by_group(data_sets):
    grouped_data_sets = {}
    for item in data_sets:
        if item['data_group'] in grouped_data_sets:
            grouped_data_sets[item['data_group']].append(item)
        else:
            grouped_data_sets[item['data_group']] = []
            grouped_data_sets[item['data_group']].append(item)
    return grouped_data_sets
