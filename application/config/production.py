import json
import os


def load_paas_settings():
    paas = {}
    if 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.environ['VCAP_SERVICES'])
        for service in vcap['user-provided']:
            if service['name'] == 'redis-poc':
                database_number = os.environ['REDIS_DATABASE_NUMBER']
                url = service['credentials']['url']
                paas['REDIS_URL'] = '{}/{}'.format(url, int(database_number))
    return paas


PAAS = load_paas_settings()

DEBUG = True
LOG_LEVEL = 'DEBUG'

VIRUS_CHECK = False
SECRET_KEY = os.getenv('SECRET_KEY')
ADMIN_HOST = os.getenv('ADMIN_HOST')
BACKDROP_HOST = os.getenv('BACKDROP_HOST')
STAGECRAFT_HOST = os.getenv('STAGECRAFT_HOST')
GOVUK_SITE_URL = os.getenv('GOVUK_SITE_URL')
SIGNON_BASE_URL = os.getenv('SIGNON_BASE_URL')
SIGNON_OAUTH_ID = os.getenv('SIGNON_OAUTH_ID')
SIGNON_OAUTH_SECRET = os.getenv('SIGNON_OAUTH_SECRET')
REDIS_URL = os.getenv('REDIS_URL') or PAAS.get('REDIS_URL')
