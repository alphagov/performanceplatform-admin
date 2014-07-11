from argh import arg
from argh.dispatching import dispatch_command
from admin import app as app


@arg('port', type=int, help='The port number to run the app on')
def start_app(port):
    app.start(port)


if __name__ == '__main__':
    dispatch_command(start_app)
