from flask.ext.testing import TestCase
from hamcrest import assert_that, equal_to

from admin import app


class FlaskAppTestCase(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app

    def assert_flashes(self, expected_message, expected_category='message'):
        assert_that(
            self.get_flashes()[1],
            equal_to(
                expected_message))
        assert_that(
            self.get_flashes()[0],
            equal_to(
                expected_category))

    def assert_session_contains(self, key, value):
        assert_that(
            self.get_from_session(key),
            equal_to(
                value))

    def get_flashes(self):
        with self.client.session_transaction() as session:
            try:
                return session['_flashes'][0]
            except KeyError:
                raise AssertionError('nothing flashed')

    def get_from_session(self, key):
        with self.client.session_transaction() as session:
            try:
                return session[key]
            except KeyError:
                raise AssertionError('nothing in session for <{}> key'.format(
                    key))
