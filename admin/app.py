from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/", methods=['GET'])
def root():
    return "Application root"


@app.route("/_status", methods=['GET'])
def status():
    return jsonify({"admin": "ok"})


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)
