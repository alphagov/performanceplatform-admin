from application import app
from application.fields.json_textarea import JSONTextAreaField
from flask_wtf import Form as FlaskWTFForm
from wtforms import (FieldList, Form, FormField, TextAreaField, TextField,
                     RadioField, BooleanField, HiddenField)
from wtforms.validators import Required, Email, URL, Optional
from wtforms_components.fields.select import SelectField
import requests
import json


def convert_to_module_for_form(module, module_types, cloned=False):
    module['info'] = json.dumps(module['info'])
    if module['query_parameters'] is not None:
        module['query_parameters'] = json.dumps(module['query_parameters'])
    module['options'] = json.dumps(module['options'])
    module['module_type'] = module['type']['id']
    if module['module_type'] == module_types.get_section_type()['id']:
        module['category'] = 'container'
    if cloned:
        module['id'] = None
    module['uuid'] = module['id']
    return module


def flatten_module(module, module_types):
    if module['type']['id'] == module_types.get_section_type()['id']:
        child_modules = module['modules']
        modules = [module]
        modules.extend(flatten_modules(child_modules, module_types))
        return modules
    else:
        return [module]


def flatten_modules(modules, module_types):
    flattened_modules = []
    for module in modules:
        flattened_modules.extend(flatten_module(module, module_types))
    return flattened_modules


def convert_to_dashboard_form(
        dashboard_dict, admin_client, module_types, data_sources):

    dashboard_dict['modules'] = flatten_modules(
        dashboard_dict['modules'],
        module_types)
    for module in dashboard_dict['modules']:
        convert_to_module_for_form(module, module_types)
    transaction_link = [link for link
                        in dashboard_dict['links']
                        if link['type'] == 'transaction']
    if len(transaction_link) > 1:
        raise ValueError('Dashboards cannot have more than 1 transaction link')
    elif len(transaction_link) == 1:
        dashboard_dict['transaction_link'] = transaction_link[0]['url']
        dashboard_dict['transaction_title'] = transaction_link[0]['title']
    if dashboard_dict.get('organisation') is not None:
        organisation_id = dashboard_dict['organisation']['id']
    else:
        organisation_id = None
    dashboard_dict['owning_organisation'] = organisation_id
    return DashboardCreationForm(admin_client,
                                 module_types,
                                 data_sources,
                                 data=dashboard_dict)


class ModuleTypes():

    def __init__(self, admin_client):
        self.types = admin_client.list_module_types()

    def get_section_type(self):
        return (module for module in self.types
                if module["name"] == "section").next()

    def get_visualisation_choices(self):
        choices = [('', '')]
        choices += [
            (module['id'], module['name'])
            for module in self.types
            if module['name'] != 'section'
        ]
        return choices


class DataSources():

    def __init__(self, admin_client, session_access_token):
        data_sets = admin_client.list_data_sets()
        sources = [
            (ds['data_group'], ds['data_type']) for ds in data_sets]
        self.sources = list(set(sources))

    def _groups(self):
        return list(set([source[0] for source in self.sources]))

    def group_choices(self):
        choices = [('', '')]
        choices += [(group, group) for group in self._groups()]
        choices.sort(key=lambda tup: tup[0])
        return choices

    def _sorted_sources(self):
        sources = list(self.sources)
        sources.sort(key=lambda tup: (tup[0], tup[1]))
        return sources

    def type_choices(self):
        choices = [('', '')]
        current_group = None
        for source in self._sorted_sources():
            if source[0] != current_group:
                choices += [(source[0], [(source[1], source[1])])]
                current_group = source[0]
            else:
                choices[-1][1].append((source[1], source[1]))
        return choices


class ModuleForm(Form):

    def __init__(self, *args, **kwargs):
        super(ModuleForm, self).__init__(*args, **kwargs)

    id = HiddenField('UUID')
    category = HiddenField('category', default='visualisation')

    module_type = SelectField('Module type')
    data_group = SelectField('Data group', default='')
    data_type = SelectField('Data type', default='')

    slug = TextField('Module URL')
    title = TextField('Title')
    description = TextField('Description')
    info = TextField('Info')

    query_parameters = JSONTextAreaField('Query parameters', default='{}')
    options = JSONTextAreaField('Visualisation settings', default='{}')


def get_organisation_choices(admin_client):
    choices = [('', '')]

    try:
        organisations = admin_client.list_organisations(
            {'type': ['department', 'agency', 'service', 'transaction']})
        choices += [
            (org['id'], org['name']) for org in organisations]
        choices.sort(key=lambda tup: tup[1])
    except requests.ConnectionError:
        if not app.config['DEBUG']:
            raise
    return choices


class DashboardCreationForm(Form):

    def __init__(
            self, admin_client, module_types, data_sources,  *args, **kwargs):
        super(DashboardCreationForm, self).__init__(*args, **kwargs)
        self.owning_organisation.choices = get_organisation_choices(
            admin_client)
        for m in self.modules:
            m.module_type.choices = module_types.get_visualisation_choices()
            m.data_group.choices = data_sources.group_choices()
            m.data_type.choices = data_sources.type_choices()

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
    slug = TextField('Dashboard URL')
    title = TextField('Dashboard title')
    description = TextField('Description')
    owning_organisation = SelectField(
        'Owning organisation',
        validators=[Required(message='This field cannot be blank.')]
    )
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
    costs = TextAreaField('Notes on costs')
    other_notes = TextAreaField('Other notes')

    transaction_title = TextField('Transaction action')
    transaction_link = TextField('Transaction link')

    modules = FieldList(FormField(ModuleForm), min_entries=0)
    published = HiddenField('published', default=False)


class AboutYouForm(FlaskWTFForm):

    def __init__(self, admin_client, *args, **kwargs):
        super(AboutYouForm, self).__init__(*args, **kwargs)
        self.organisation.choices = get_organisation_choices(
            admin_client)
        self.organisation.choices[0] = ('', 'Select a department or agency')

    full_name = TextField(
        'Full name',
        validators=[Required(message='Name cannot be blank')])
    email_address = TextField(
        'Email address',
        validators=[
            Required(message='Email cannot be blank'),
            Email(message='Email format is invalid')
        ])
    organisation = SelectField(
        'Your organisation',
        validators=[Required(message='Organisation cannot be blank')]
    )


class AboutYourServiceForm(FlaskWTFForm):
    service_name = TextField(
        'Service name',
        validators=[Required(message='Name cannot be blank')])
    service_url = TextField(
        'Service start page URL',
        validators=[
            Optional(),
            URL(message='Start page URL format is invalid')
        ])
    service_description = TextAreaField(
        'Service description',
        validators=[Required(message='Service description cannot be blank')])


class DonePageURLForm(FlaskWTFForm):
    done_page_url = TextField(
        'Done page URL',
        validators=[
            URL(message='Done page URL format is invalid'),
            Required(message='Done page URL cannot be blank')
        ])


class DashboardHubForm(FlaskWTFForm):
    title = TextField(
        'Dashboard title',
        validators=[Required(message='Title cannot be blank')])
    description = TextAreaField(
        'Dashboard description',
        validators=[Required(message='Description cannot be blank')])


class UploadOptionsForm(FlaskWTFForm):
    upload_option = RadioField(
        '',
        choices=[
            ('api', "Automatically upload from your transaction's API"),
            ('week', 'Manually upload a spreadsheet every week'),
            ('month', 'Manually upload a spreadsheet every month')
        ],
        default='week',
        validators=[Required(message='Please select an upload option')])


class ChannelOptionsForm(FlaskWTFForm):
    digital = BooleanField('Website')
    api = BooleanField('Api')
    telephone_human = BooleanField('Telephone (human operator)')
    telephone_automated = BooleanField('Telephone (automated)')
    paper_form = BooleanField('Paper form')
    face_to_face = BooleanField('Face to face')


class UploadDataForm(FlaskWTFForm):
    pass
