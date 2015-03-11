#!/bin/bash -e

basedir=$(dirname $0)

export TESTING=1

pip install -r requirements_for_tests.txt

nosetests -s -v --with-xunit --with-coverage --cover-package=application

if [ -z "$NO_AUTOPEP8" ]; then
  autopep8 -i -r application tests
fi

pep8 --exclude=venv,build "$basedir"
