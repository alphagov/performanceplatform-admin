COOKIE_SECRET_KEY = 'placeholder_cookie_secret_key'

ADMIN_HOST = 'https://admin-beta.development.performance.service.gov.uk'

BACKDROP_HOST = 'http://www.development.performance.service.gov.uk'
STAGECRAFT_HOST = 'http://stagecraft.development.performance.service.gov.uk'

GOVUK_SITE_URL = 'http://spotlight.development.performance.service.gov.uk'
SIGNON_OAUTH_ID = 'oauth_id'
SIGNON_OAUTH_SECRET = 'oauth_secret'
SIGNON_BASE_URL = 'http://signon.dev.gov.uk'

DEBUG = True

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

FAKE_OAUTH_TOKEN = 'development-oauth-access-token'
FAKE_OAUTH_USER = {
    "email": "some.user@digital.cabinet-office.gov.uk",
    "name": "Some User",
    "organisation_slug": "cabinet-office",
    "permissions": [
        "signin",
        "user",
        "admin",
        "dashboard",
    ],
    "uid": "00000000-0000-0000-0000-000000000000"
}

AWS_ACCESS_KEY_ID = 'AWS access key id'
AWS_SECRET_ACCESS_KEY = 'AWS secret access key'
NOTIFICATIONS_EMAIL = 'notifications@performance.service.gov.uk'
NO_REPLY_EMAIL = 'no-reply@performance.service.gov.uk'

# You can use development_local_overrides.py in this directory to set config
# that is unique to your development environment, like OAuth IDs and secrets.
# It is not in version control.
try:
    from development_local_overrides import *
except ImportError as e:
    pass
