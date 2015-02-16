from unittest import TestCase
from admin.forms import convert_to_dashboard_form, DataSources
from hamcrest import assert_that, equal_to, contains_inanyorder, contains
from mock import Mock
import os
import json
from admin.dashboards import build_dict_for_post
from tests.admin.test_dashboards import data_sets_list


class DashboardTestCase(TestCase):
    def setUp(self):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../fixtures/example-dashboard.json')) as file:
            self.dashboard_json = file.read()
        self.mock_admin_client = Mock()
        self.mock_admin_client.list_organisations = Mock(
            return_value=[{'id': '', 'name': ''}])
        self.mock_module_types = Mock()
        self.mock_module_types.get_section_type = Mock(
            return_value={
                'id': 'section-module-type-uuid', 'name': 'section'})
        self.mock_data_sources = Mock()

    def test_convert_to_dashboard_form_returns_correct_dashboard_form(self):
        dashboard_dict = json.loads(self.dashboard_json)
        dashboard_form = convert_to_dashboard_form(dashboard_dict,
                                                   self.mock_admin_client,
                                                   self.mock_module_types,
                                                   self.mock_data_sources)
        dict_for_post = build_dict_for_post(dashboard_form,
                                            self.mock_module_types)
        assert_that(
            dict_for_post['description'],
            equal_to(dashboard_dict['description']))
        assert_that(
            dict_for_post['dashboard-type'],
            equal_to(dashboard_dict['dashboard_type']))
        assert_that(
            dict_for_post['modules'][0]['type_id'],
            equal_to(dashboard_dict['modules'][0]['type']['id']))
        assert_that(
            dict_for_post['modules'][0]['data_group'],
            equal_to(dashboard_dict['modules'][0]['data_group']))
        assert_that(
            dict_for_post['modules'][0]['data_type'],
            equal_to(dashboard_dict['modules'][0]['data_type']))
        assert_that(
            dict_for_post['modules'][0]['id'],
            equal_to(dashboard_dict['modules'][0]['id']))
        assert_that(
            dict_for_post['modules'][0]['description'],
            equal_to(dashboard_dict['modules'][0]['description']))
        assert_that(
            dict_for_post['links'], equal_to(dashboard_dict['links']))
        assert_that(
            dict_for_post['published'], equal_to(dashboard_dict['published']))

    def test_convert_to_dashboard_form_returns_flattened_modules(self):
        dashboard_dict = json.loads(self.dashboard_json)
        dashboard_form = convert_to_dashboard_form(dashboard_dict,
                                                   self.mock_admin_client,
                                                   self.mock_module_types,
                                                   self.mock_data_sources)
        modules = dashboard_form.modules
        assert_that(len(modules), equal_to(6))
        assert_that(modules[-2].data['title'], equal_to('Digital services'))
        assert_that(modules[-1].data['title'], equal_to('Digital take-up'))


class DataSourcesTestCase(TestCase):
    def setUp(self):
        mock_admin_client = Mock()
        mock_admin_client.list_data_sets = Mock(
            return_value=data_sets_list())
        self.data_sources = DataSources(mock_admin_client, 'foo')

    def test_derives_sources_from_data_sets(self):
        sources = self.data_sources.sources
        assert_that(sources, contains_inanyorder(
            ('vehicle-licensing', 'channels'),
            ('vehicle-licensing', 'failures'),
            ('carers-allowance', 'realtime')))

    def tests_builds_sorted_group_choices_without_duplicates(self):
        choices = self.data_sources.group_choices()
        assert_that(choices, contains(
            ('', ''),
            ('carers-allowance', 'carers-allowance'),
            ('vehicle-licensing', 'vehicle-licensing')))

    def test_builds_sorted_data_type_choices_by_group(self):
        choices = self.data_sources.type_choices()
        assert_that(choices, contains(
            ('', ''),
            ('carers-allowance', [
                ('realtime', 'realtime')]),
            ('vehicle-licensing', [
                ('channels', 'channels'), ('failures', 'failures')])))
