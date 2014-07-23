from os import path
import scss

# if this file is always at the root of the project
project_root = path.dirname(path.dirname(path.realpath(__file__)))

scss.config.LOAD_PATHS = [
    path.join(project_root, 'admin/assets/scss')]

# compress does not seem to be working
scss_compiler = scss.Scss(
    scss_opts={
        'compress': True,
    })

compiled_css_from_file = scss_compiler.compile(
    scss_file=path.join(
        project_root,
        'admin/assets/scss/manifest/govuk_admin_template.scss'))

css_path = path.join(
    project_root,
    'admin/static/css/govuk_admin_template.css')

with open(css_path, 'w') as file:
    file.write(compiled_css_from_file)
