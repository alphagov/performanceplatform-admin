from unittest import TestCase
from admin.forms import convert_to_dashboard_form
from hamcrest import assert_that, equal_to
from mock import Mock
import os
import json
from admin.dashboards import build_dict_for_post


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

    def test_convert_to_dashboard_form_returns_correct_dashboard_form(self):
        dashboard_dict = json.loads(self.dashboard_json)
        dashboard_form = convert_to_dashboard_form(dashboard_dict,
                                                   self.mock_admin_client,
                                                   self.mock_module_types)
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
                                                   self.mock_module_types)
        modules = dashboard_form.modules
        assert_that(len(modules), equal_to(6))
        assert_that(modules[-2].data['title'], equal_to('Digital services'))
        assert_that(modules[-1].data['title'], equal_to('Digital take-up'))
