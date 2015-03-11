from tests.admin.support.flask_app_test_case import FlaskAppTestCase
from mock import patch
from hamcrest import (assert_that, equal_to, contains_string,
                      ends_with)
from admin import app


class StartPageTestCase(FlaskAppTestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_register_slug_renders_start_page(self):
        response = self.app.get('/register')
        assert_that(response.status, equal_to('200 OK'))


def organisations_list():
    return [{'id': 'organisation-uuid', 'name': 'Mock organisation'}]


@patch("performanceplatform.client.admin.AdminAPI.list_organisations",
       return_value=organisations_list())
class AboutYouPageTestCase(FlaskAppTestCase):

    def setUp(self):
        self.app = app.test_client()
        app.config['WTF_CSRF_ENABLED'] = False

    @staticmethod
    def params(options={}):
        params = {
            'full_name': 'Foo Bar',
            'email_address': 'foo@example.com',
            'organisation': 'organisation-uuid'
        }
        params.update(options)
        return params

    def test_about_you_slug_renders_about_you_page(
            self, mock_list_organisations):
        response = self.app.get('/register/about-you')
        assert_that(response.status, equal_to('200 OK'))

    def test_full_name_field_is_required(self, mock_list_organisations):
        data = self.params({'full_name': ''})
        response = self.app.post('/register/about-you', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Name cannot be blank'))

    def test_email_address_field_is_required(self, mock_list_organisations):
        data = self.params({'email_address': ''})
        response = self.app.post('/register/about-you', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Email cannot be blank'))

    def test_email_address_is_like_an_email_address(
            self, mock_list_organisations):
        data = self.params({'email_address': 'foo.example.com'})
        response = self.app.post('/register/about-you', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Email format is invalid'))

    def test_organisation_field_is_required(self, mock_list_organisations):
        data = self.params({'organisation': ''})
        response = self.app.post('/register/about-you', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(
            response.data, contains_string('Organisation cannot be blank'))

    def test_stores_submitted_data_in_the_session(
            self, mock_list_organsations):
        self.client.post('/register/about-you', data=self.params())
        self.assert_session_contains('full_name', 'Foo Bar')
        self.assert_session_contains('email_address', 'foo@example.com')
        self.assert_session_contains('organisation_name', 'Mock organisation')

    def test_redirects_to_about_your_service_page(
            self, mock_list_organisations):
        response = self.app.post('/register/about-you', data=self.params())
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/about-your-service'))


@patch("boto.ses.connect_to_region")
class AboutYourServicePageTestCase(FlaskAppTestCase):

    def setUp(self):
        self.app = app.test_client()
        app.config['WTF_CSRF_ENABLED'] = False
        with self.client.session_transaction() as session:
            session['full_name'] = 'Foo Bar'
            session['email_address'] = 'foo@example.com'
            session['organisation_name'] = 'Mock organisation'

    @staticmethod
    def params(options={}):
        params = {
            'service_name': 'Foo',
            'service_url': '',
            'service_description': 'All about foo'
        }
        params.update(options)
        return params

    def test_service_name_field_is_required(self, mock_ses_connection):
        data = self.params({'service_name': ''})
        response = self.client.post('/register/about-your-service', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data, contains_string('Name cannot be blank'))

    def test_service_url_field_is_optional(self, mock_ses_connection):
        data = self.params()
        response = self.client.post('/register/about-your-service', data=data)
        assert_that(response.status, equal_to('302 FOUND'))

    def test_service_url_is_like_a_url(self, mock_ses_connection):
        data = self.params({'service_url': 'www.foo..com'})
        response = self.client.post('/register/about-your-service', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data,
                    contains_string('Start page URL format is invalid'))

    def test_service_description_field_is_required(self, mock_ses_connection):
        data = self.params({'service_description': ''})
        response = self.client.post('/register/about-your-service', data=data)
        assert_that(response.status, equal_to('200 OK'))
        assert_that(response.data,
                    contains_string('Service description cannot be blank'))

    def test_stores_submitted_data_in_the_session(self, mock_ses_connection):
        self.client.post('/register/about-your-service', data=self.params())
        self.assert_session_contains('service_name', 'Foo')
        self.assert_session_contains('service_url', '')
        self.assert_session_contains('service_description', 'All about foo')

    def test_sends_details_of_the_application_by_email(
            self, mock_ses_connection):
        data = self.params({'service_url': 'http://www.foo.com'})
        self.client.post('/register/about-your-service', data=data)
        second_call_args = mock_ses_connection.mock_calls[1][1]
        assert_that(second_call_args[0],
                    equal_to(app.config['NO_REPLY_EMAIL']))
        assert_that(second_call_args[1], equal_to('New dashboard application'))
        assert_that(second_call_args[2],
                    contains_string('Full name: Foo Bar\n'))
        assert_that(second_call_args[2],
                    contains_string('Email address: foo@example.com\n'))
        assert_that(second_call_args[2],
                    contains_string('Organisation name: Mock organisation\n'))
        assert_that(second_call_args[2],
                    contains_string('Service name: Foo\n'))
        assert_that(second_call_args[2],
                    contains_string('Service URL: http://www.foo.com\n'))
        assert_that(second_call_args[2],
                    contains_string('Service description:\nAll about foo'))
        assert_that(
            second_call_args[3],
            equal_to(app.config['NOTIFICATIONS_EMAIL']))

    def test_redirects_to_confirmation_page(self, mock_ses_connection):
        data = self.params()
        response = self.client.post('/register/about-your-service', data=data)
        assert_that(response.status, equal_to('302 FOUND'))
        assert_that(response.headers['Location'],
                    ends_with('/confirmation'))


class ConfirmationPageTestCase(FlaskAppTestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_confirmation_slug_renders_confirmation_page(self):
        response = self.app.get('/register/confirmation')
        assert_that(response.status, equal_to('200 OK'))

    def test_resets_session_data(self):
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        with self.client.session_transaction() as session:
            session['full_name'] = ''
            session['email_address'] = ''
            session['organisation_name'] = ''
            session['service_name'] = ''
            session['service_url'] = ''
            session['service_description'] = ''
        self.client.get('/register/confirmation')
        self.assert_session_does_not_contain('full_name')
        self.assert_session_does_not_contain('email_address')
        self.assert_session_does_not_contain('organisation_name')
        self.assert_session_does_not_contain('service_name')
        self.assert_session_does_not_contain('service_url')
        self.assert_session_does_not_contain('service_description')
