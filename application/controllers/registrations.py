from flask import (session, render_template, url_for, flash, redirect)
import boto.ses
from application import app
from performanceplatform.client.admin import AdminAPI
from application.forms import AboutYouForm, AboutYourServiceForm
from application.helpers import base_template_context, to_error_list

REGISTER_ROUTE = '/register'


@app.route('{0}'.format(REGISTER_ROUTE), methods=['GET'])
def start():
    template_context = base_template_context()
    return render_template('registrations/start.html', **template_context)


@app.route('{0}/about-you'.format(REGISTER_ROUTE), methods=['GET', 'POST'])
def about_you():
    admin_client = AdminAPI(app.config['STAGECRAFT_HOST'], None)
    form = AboutYouForm(admin_client)
    template_context = base_template_context()
    if form.validate_on_submit():
        session['full_name'] = form.data['full_name']
        session['email_address'] = form.data['email_address']
        session['organisation_name'] = get_organisation_name(
            form.data['organisation'], form.organisation.choices)
        return redirect(url_for('about_your_service'))
    if form.errors:
        flash(to_error_list(form.errors), 'danger')
    return render_template(
        'registrations/about-you.html',
        form=form,
        **template_context)


def get_organisation_name(uuid, choices):
    return [i[1] for i in choices if i[0] == uuid][0]


@app.route('{0}/about-your-service'.format(REGISTER_ROUTE),
           methods=['GET', 'POST'])
def about_your_service():
    form = AboutYourServiceForm()
    template_context = base_template_context()
    if form.validate_on_submit():
        session['service_name'] = form.data['service_name']
        session['service_url'] = form.data['service_url']
        session['service_description'] = form.data['service_description']
        send_application_email()
        return redirect(url_for('confirmation'))
    if form.errors:
        flash(to_error_list(form.errors), 'danger')
    return render_template(
        'registrations/about-your-service.html',
        form=form,
        **template_context)


def send_application_email():
    conn = boto.ses.connect_to_region(
        'us-east-1',
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])

    body_text = (
        "Full name: {0}\n\n"
        "Email address: {1}\n\n"
        "Organisation name: {2}\n\n"
        "Service name: {3}\n\n"
        "Service URL: {4}\n\n"
        "Service description:\n{5}").format(
            session['full_name'],
            session['email_address'],
            session['organisation_name'],
            session['service_name'],
            session['service_url'],
            session['service_description'])

    conn.send_email(
        app.config['NO_REPLY_EMAIL'],
        'New dashboard application',
        body_text,
        app.config['NOTIFICATIONS_EMAIL'],
        reply_addresses=app.config['NO_REPLY_EMAIL'])


@app.route('{0}/confirmation'.format(REGISTER_ROUTE), methods=['GET'])
def confirmation():
    session.pop('full_name', None)
    session.pop('email_address', None)
    session.pop('organisation_name', None)
    session.pop('service_name', None)
    session.pop('service_url', None)
    session.pop('service_description', None)
    template_context = base_template_context()
    return render_template(
        'registrations/confirmation.html',
        **template_context)
