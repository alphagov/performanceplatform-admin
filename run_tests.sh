#!/bin/bash -e

basedir=$(dirname $0)

pip install -r requirements_for_tests.txt

nosetests -v --with-xunit --with-coverage --cover-package=admin

pep8 --exclude=venv "$basedir"
