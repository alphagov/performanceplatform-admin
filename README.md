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

This should also automatically compile sass to `admin/static/css/govuk_admin_template.css` when run in development

You can modify your local configuration without affecting version control using
the instructions in the `admin/config/development.py` file.

## Running tests

```bash
./run_tests.sh
```

## Getting set up with signonotron2

1. Create [signon application and user](https://github.com/alphagov/signonotron2#usage)
2. Update [development config](https://github.com/alphagov/performanceplatform-admin/blob/master/admin/config/development.py) with OAuth2 credentials.
3. Run app with OAUTHLIB_INSECURE_TRANSPORT environment variable set `OAUTHLIB_INSECURE_TRANSPORT=1 python start.py 3070`

## Compiling scss 

If you need to compile scss outside of the normal app starting process then run:

```bash
python tools/compile_sass.py
```
