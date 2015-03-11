from os import path
import logging
import scss

logging.basicConfig()

project_root = path.dirname(path.dirname(path.realpath(__file__)))

scss.config.LOAD_PATHS = [
    path.join(project_root, 'admin/assets/scss')]

scss_compiler = scss.Scss()

compiled_css_from_file = scss_compiler.compile(
    scss_file=path.join(
        project_root,
        'admin/assets/scss/manifest/performanceplatform-admin.scss'))

css_path = path.join(
    project_root,
    'admin/static/css/performanceplatform-admin.css')

with open(css_path, 'w') as file:
    file.write(compiled_css_from_file.encode('utf-8'))
