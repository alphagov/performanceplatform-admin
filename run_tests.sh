#!/bin/bash -e

basedir=$(dirname $0)

pip install -r requirements_for_tests.txt

pep8 "$basedir"
