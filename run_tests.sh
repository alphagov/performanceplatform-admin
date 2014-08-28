#!/bin/bash -e

basedir=$(dirname $0)

pip install -r requirements_for_tests.txt

find . -name '*.pyc' -delete

nosetests -s -v --with-xunit --with-coverage --cover-package=admin

pep8 --exclude=venv "$basedir"
