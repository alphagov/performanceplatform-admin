from admin import app
from admin.main import requires_authentication
from flask import render_template


@app.route('/upload-data', methods=['GET'])
@requires_authentication
def upload_list_data_sets(session_context):
    return render_template('data_sets.html', **session_context)
