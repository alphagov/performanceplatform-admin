from argh import arg
from argh.dispatching import dispatch_command
import admin


@arg('port', type=int, help='The port number to run the app on')
def start_app(port):
    admin.start(port)


if __name__ == '__main__':
    dispatch_command(start_app)
