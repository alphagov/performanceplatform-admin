from flask import (
    url_for
)
from requests import HTTPError
from application.controllers.upload import (
    response
)
from application.controllers.upload import (
    upload_file_and_get_status
)


def upload_data_and_respond(
        admin_client,
        data_type,
        data_group,
        uuid,
        module_name,
        data_set=None):
    if not data_set:
        try:
            data_set = admin_client.get_data_set(data_group, data_type)
        except HTTPError as err:
            return response(500, data_group, data_type,
                            ['[{}] {}'.format(err.response.status_code,
                                              err.response.json())],
                            url_for(
                                'upload_{}_file'.format(module_name),
                                uuid=uuid))

    messages, status = upload_file_and_get_status(data_set)

    if messages:
        return response(status, data_group, data_type, messages,
                        url_for('upload_{}'.format(module_name),
                                uuid=uuid))

    return response(status, data_group, data_type, messages,
                    url_for('upload_{}_success'.format(module_name),
                            uuid=uuid))
