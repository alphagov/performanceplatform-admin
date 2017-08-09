#!/bin/bash -e

basedir=$(dirname $0)

export TESTING=1
export GOVUK_ENV=development
export REDIS_URL='redis://localhost:6379/12'

pip install -U pip wheel
pip install -r requirements_for_tests.txt

nosetests -s -v --with-xunit --with-coverage --cover-package=application

#if [ -z "$NO_AUTOPEP8" ]; then
#  autopep8 -i -r application tests
#fi
#
#pep8 --exclude=venv,build "$basedir"
