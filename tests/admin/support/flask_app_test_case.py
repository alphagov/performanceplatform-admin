from flask.ext.testing import TestCase

from admin import app


class FlaskAppTestCase(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app
