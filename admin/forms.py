from admin import app
from wtforms import (FieldList, Form, FormField, TextAreaField, TextField,
                     SelectField)

import requests


def get_module_choices():
    # FIXME: If Stagecraft isn't running when it tries to make this request,
    #        the list of available modules will be empty.
    module_path = '{0}/module-type'.format(app.config['STAGECRAFT_HOST'])
    modules = requests.get(module_path)

    if modules.status_code == 200:
        module_json = modules.json()
        default_list = [('', '')]
        module_list = [(module['id'], module['name']) for module in module_json]
        return default_list + module_list
    else:
        return [('', '')]


class ModuleForm(Form):
    module_type = SelectField('Module type', choices=get_module_choices())

    data_group = TextField('Data group')
    data_type = TextField('Data type')

    slug = TextField('Slug')
    title = TextField('Title')
    module_description = TextField('Description')
    info = TextField('Info')

    query_parameters = TextAreaField('Query parameters', default='{}')
    options = TextAreaField('Options', default='{}')


class DashboardCreationForm(Form):
    dashboard_type = SelectField('Dashboard type', choices=[
        ('transaction', 'Transaction'),
        ('high-volume-transaction', 'High volume transaction'),
        ('service-group', 'Service group'),
        ('agency', 'Agency'),
        ('department', 'Department'),
        ('content', 'Content'),
        ('other', 'Other'),
    ])
    strapline = SelectField('Strapline', choices=[
        ('Dashboard', 'Dashboard'),
        ('Service dashboard', 'Service dashboard'),
        ('Content dashboard', 'Content dashboard'),
        ('Performance', 'Performance'),
        ('Policy dashboard', 'Policy dashboard'),
        ('Public sector purchasing dashboard',
         'Public sector purchasing dashboard'),
    ])
    slug = TextField('Slug')
    title = TextField('Title')
    description = TextField('Description')
    customer_type = SelectField('Customer type', choices=[
        ('', ''),
        ('Business', 'Business'),
        ('Individuals', 'Individuals'),
    ])
    business_model = SelectField('Business model', choices=[
        ('', ''),
        ('Department budget', 'Department budget'),
        ('Fees and charges', 'Fees and charges'),
        ('Taxpayers', 'Taxpayers'),
        ('Fees and charges, and taxpayers', 'Fees and charges, and taxpayers'),
    ])

    transaction_title = TextField('Transaction action')
    transaction_link = TextField('Transaction link')

    modules = FieldList(FormField(ModuleForm), min_entries=0)
