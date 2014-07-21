# Performance Platform admin

[![Build status](https://travis-ci.org/alphagov/performanceplatform-admin.svg?branch=master)](https://travis-ci.org/alphagov/performanceplatform-admin)
[![Coverage Status](https://coveralls.io/repos/alphagov/performanceplatform-admin/badge.png)](https://coveralls.io/r/alphagov/performanceplatform-admin)

Performance Platform admin is a [Flask][] app that allows authorised
users to update [performance data on GOV.UK][pp].

[Flask]: http://flask.pocoo.org/
[pp]: https://www.gov.uk/performance

## Installing dependencies

We recommend using [virtualenv][] to manage this application's dependencies.

To set up, run:

```bash
pip install -r requirements.txt
```

[virtualenv]: http://virtualenv.readthedocs.org/

## Running the app

```bash
python start.py 3070
```

## Running tests

```bash
./run_tests.sh
```
