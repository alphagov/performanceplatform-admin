import os

from argh.dispatching import dispatch_command

import application


def start_app():
    port = int(os.getenv('PORT'))
    application.start(port=port)


if __name__ == '__main__':
    dispatch_command(start_app)
