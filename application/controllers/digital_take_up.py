from application import app
from application.forms import UploadOptionsForm, ChannelOptionsForm
from flask import (
    session,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    make_response
)
from application.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
    to_error_list
)
from application.utils.datetimeutil import (
    a_week_ago,
    a_month_ago,
    start_of_week,
    start_of_month,
    to_datetime
)

DASHBOARD_ROUTE = '/dashboard'


@app.route(
    '{0}/<uuid>/digital-take-up/upload-options'.format(DASHBOARD_ROUTE),
    methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def upload_options(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    form = UploadOptionsForm()
    if form.validate_on_submit():
        session['upload_choice'] = form.data['upload_option']
        if session['upload_choice'] != 'api':
            return redirect(url_for('channel_options', uuid=uuid))
        else:
            return redirect(url_for('api_get_in_touch', uuid=uuid))
    if form.errors:
        flash(to_error_list(form.errors), 'danger')
    return render_template(
        'digital_take_up/upload-options.html',
        uuid=uuid,
        upload_options=[option for option in form.upload_option],
        form=form,
        **template_context)


@app.route(
    '{0}/<uuid>/digital-take-up/api-get-in-touch'.format(DASHBOARD_ROUTE))
@requires_authentication
@requires_permission('dashboard')
def api_get_in_touch(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user']
    })
    return render_template(
        'digital_take_up/api-get-in-touch.html',
        email=app.config['NOTIFICATIONS_EMAIL'],
        uuid=uuid,
        **template_context)


@app.route(
    '{0}/<uuid>/digital-take-up/channel-options'.format(DASHBOARD_ROUTE),
    methods=['GET', 'POST'])
@requires_authentication
@requires_permission('dashboard')
def channel_options(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })
    form = ChannelOptionsForm()
    if request.method == 'POST':
        if True in form.data.values():
            session['channel_choices'] = [
                key for key, val in form.data.items() if val]
            return redirect(url_for('upload_digital_take_up_data_file', uuid=uuid))
        else:
            error = 'Please select one or more channel options.'
            flash(error, 'danger')
    return render_template(
        'digital_take_up/channel-options.html',
        uuid=uuid,
        form=form,
        **template_context)

@app.route(
    '{0}/<uuid>/digital-take-up/spreadsheet-template'.format(DASHBOARD_ROUTE))
@requires_authentication
@requires_permission('dashboard')
def spreadsheet_template(admin_client, uuid):
    csv = make_csv()
    response = make_response(csv)
    response.headers[
        "Content-Disposition"] = "attachment; filename=digital_take_up.csv"
    return response


def make_csv():
    csv = "_timestamp,period,channel,count\n"
    if session['upload_choice'] == 'week':
        start_date = start_of_week(a_week_ago())
    else:
        start_date = start_of_month(a_month_ago())
    timestamp = to_datetime(start_date).isoformat()
    for channel in session['channel_choices']:
        csv += '{0},{1},{2},0\n'.format(
            timestamp,
            session['upload_choice'],
            channel)
    return csv
