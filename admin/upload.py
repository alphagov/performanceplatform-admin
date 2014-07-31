from admin import app
from admin.main import get_context
from flask import session, render_template


@app.route('/upload-data', methods=['GET'])
@requires_authentication
def upload_list_data_sets():
    return render_template('data_sets.html', **get_context(session))
