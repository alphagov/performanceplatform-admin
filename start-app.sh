#!/bin/bash -e

echo "Installing dependencies"
pip install -r requirements.txt

echo "Starting app"
exec python start.py $APP_PORT
