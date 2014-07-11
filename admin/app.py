from flask import Flask

app = Flask(__name__)


@app.route("/", methods=['GET'])
def root():
    return "Application root"


@app.route("/_status", methods=['GET'])
def status():
    return "Status endpoint"


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)
