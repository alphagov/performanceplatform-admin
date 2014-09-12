from flask.ext.testing import TestCase
from hamcrest import assert_that, equal_to
from functools import wraps

from admin import app


def signed_in(f):
    @wraps(f)
    def set_session_signed_in(*args, **kwargs):
        self = args[0]
        with self.client as client:
            with client.session_transaction() as sess:
                sess.update({
                    'oauth_token': {
                        'access_token': 'token'
                    },
                    'oauth_user': {
                        'permissions': ['signin']
                    }
                })
            kwargs['client'] = client
            return f(*args, **kwargs)
    return set_session_signed_in


class FlaskAppTestCase(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app

    def assert_flashes(self, expected_message, expected_category='message'):
        assert_that(
            self.get_first_flash()[1],
            equal_to(
                expected_message))
        assert_that(
            self.get_first_flash()[0],
            equal_to(
                expected_category))

    def assert_session_contains(self, key, value):
        try:
            session_item = self.get_from_session(key)
        except KeyError:
            raise AssertionError('Nothing in session for <{}> key'.format(key))

        assert_that(session_item, equal_to(value))

    def assert_session_does_not_contain(self, key):
        self.assertRaises(KeyError, self.get_from_session, key)

    def get_first_flash(self):
        try:
            return self.get_flashes()[0]
        except KeyError:
            raise AssertionError('nothing flashed')

    def get_flashes(self):
        with self.client.session_transaction() as session:
            if '_flashes' in session:
                return session['_flashes']
            else:
                return []

    def get_from_session(self, key):
        with self.client.session_transaction() as session:
            return session[key]
