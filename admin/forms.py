from admin import app
from admin.fields.json_textarea import JSONTextAreaField
from wtforms import (FieldList, Form, FormField, TextAreaField, TextField,
                     HiddenField, validators)
from wtforms_components.fields.select import SelectField
from performanceplatform.client import AdminAPI
import requests
import json


def convert_to_dashboard_form(
        dashboard_dict, admin_client, module_types, data_sources):
    def flatten_modules(modules):
        flattened_modules = []
        for module in modules:
            if module['type']['id'] == module_types.get_section_type()['id']:
                child_modules = module['modules']
                flattened_modules.append(module)
                flattened_modules.extend(flatten_modules(child_modules))
            else:
                flattened_modules.append(module)
        return flattened_modules

    dashboard_dict['modules'] = flatten_modules(dashboard_dict['modules'])
    for module in dashboard_dict['modules']:
        module['info'] = json.dumps(module['info'])
        if module['query_parameters'] is not None:
            module['query_parameters'] = json.dumps(module['query_parameters'])
        module['options'] = json.dumps(module['options'])
        module['module_type'] = module['type']['id']
        if module['module_type'] == module_types.get_section_type()['id']:
            module['category'] = 'container'
        module['uuid'] = module['id']
    transaction_link = [link for link
                        in dashboard_dict['links']
                        if link['type'] == 'transaction']
    if len(transaction_link) > 1:
        raise ValueError('Dashboards cannot have more than 1 transaction link')
    elif len(transaction_link) == 1:
        dashboard_dict['transaction_link'] = transaction_link[0]['url']
        dashboard_dict['transaction_title'] = transaction_link[0]['title']
    if dashboard_dict['organisation'] is not None:
        organisation_id = dashboard_dict['organisation']['id']
    else:
        organisation_id = None
    dashboard_dict['owning_organisation'] = organisation_id
    return DashboardCreationForm(admin_client,
                                 module_types,
                                 data_sources,
                                 data=dashboard_dict)


class ModuleTypes():
    def __init__(self):
        self.types_cache = None

    def get_types(self):
        if self.types_cache is None:
            self.types_cache = []
            try:
                admin_client = AdminAPI(
                    app.config['STAGECRAFT_HOST'], None)
                self.types_cache = admin_client.list_module_types()
            except requests.ConnectionError:
                if not app.config['DEBUG']:
                    raise
        return self.types_cache

    def get_section_type(self):
        return (module for module in self.get_types()
                if module["name"] == "section").next()

    def get_visualisation_choices(self):
        choices = [('', '')]
        choices += [
            (module['id'], module['name'])
            for module in self.get_types()
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
        organisations = admin_client.list_organisations()
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
        [validators.Required(message='This field cannot be blank.')]
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
