from unittest import TestCase
from admin.forms import convert_to_dashboard_form
from hamcrest import assert_that, equal_to
import os
import json
from admin.dashboards import build_dict_for_post


class DashboardTestCase(TestCase):
    def test_convert_to_dashboard_form_returns_correct_dashboard_form(self):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../fixtures/example-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        dashboard_form = convert_to_dashboard_form(dashboard_dict)
        # stuff
        dict_for_post = build_dict_for_post(form)
        # stuff
        assert_that(dashboard_form.description.data, equal_to(dashboard_dict['description']))
        assert_that(dashboard_form.dashboard_type.data, equal_to(dashboard_dict['description']))
        assert_that(dict_for_post.description, equal_to(dashboard_dict['description']))
        assert_that(dict_for_post.dashboard_type, equal_to(dashboard_dict['description']))


