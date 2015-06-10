import random
import string
from werkzeug.utils import redirect
from application import app
from flask import abort, session, redirect, request, url_for, flash
from functools import wraps
from os import getenv
from performanceplatform.client.admin import AdminAPI
from requests_oauthlib import OAuth2Session
from requests import Timeout, ConnectionError


environment = app.config.get('ENVIRONMENT', 'development')


@app.context_processor
def view_helpers():
    def can_edit_dashboards(user):
        return 'permissions' in user and \
            'dashboard' in user['permissions']

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
    """
    Used for application level requests from a client.
    """
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


def api_permission_required(permission=None):
    """
    Used for API level requests originating from signonotron.
    """
    def decorator(f):
        @wraps(f)
        def verify_api_user_has_permission(*args, **kwargs):
            if permission is None:
                raise Exception('@api_permission_required needs an argument')

            access_token = _extract_bearer_token(request)

            if access_token is None:
                abort(401, 'no access token given.')

            user = _get_user(access_token)

            if user is None:
                # This is very unexpected, since we expect the token to come
                # from signonotron. Possibly under attack, or crossing the
                # environments?
                abort(401, 'invalid access token.')

            if permission in user['user']['permissions']:
                session['oauth_user'] = user['user']
                session['oauth_token'] = {
                    'access_token': access_token
                }
                return f(*args, **kwargs)
            else:
                abort(403, 'user lacks permission.')

        return verify_api_user_has_permission

    return decorator


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


def _extract_bearer_token(request):
    auth_header = request.headers.get('Authorization', None)
    if auth_header is None:
        return None

    return _get_valid_token(auth_header)


def _get_valid_token(auth_header):
    """
    >>> _get_valid_token(u'Bearer some-token') == 'some-token'
    True
    >>> _get_valid_token('Bearer ') is None
    True
    >>> _get_valid_token('Something Else') is None
    True
    """
    prefix = 'Bearer '
    if not auth_header.startswith(prefix):
        return None

    token = auth_header[len(prefix):]
    return token if len(token) else None


def _get_user(token):
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
        return user_request.json()
    except ValueError:
        abort(500, 'Unable to parse signon json')


def to_error_list(form_errors):
    def format_error(error):
        return '{0}'.format(error)

    messages = []
    for field_name, field_errors in form_errors.items():
        messages.append('; '.join(map(format_error, field_errors)))
    return 'You have errors in your form: ' + '; '.join(messages) + '.'


@app.template_filter('format_status')
def format_status(s):
    return s.title().replace('-', ' ')


def generate_bearer_token():
    return ''.join(random.choice(string.lowercase + string.digits)
                   for i in range(64))


def redirect_if_module_exists(module_name):
    def wrap(func):
        @wraps(func)
        def check_and_redirect(*args, **kwargs):
            admin_client = kwargs['admin_client']
            uuid = kwargs['uuid']
            dashboard_dict = admin_client.get_dashboard(uuid)
            if "modules" in dashboard_dict.keys():
                data_types = [module["data_type"]
                              for module in dashboard_dict["modules"]]
                if module_name in data_types:
                    flash("Module already exists", 'info')
                    return redirect(url_for(
                        'dashboard_hub', uuid=uuid))
            return func(*args, **kwargs)
        return check_and_redirect
    return wrap
