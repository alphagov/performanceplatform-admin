#!/bin/bash -e

basedir=$(dirname $0)

export TESTING=1

pip install -r requirements_for_tests.txt

nosetests -s -v --with-xunit --with-coverage --cover-package=admin

pep8 --exclude=venv "$basedir"
