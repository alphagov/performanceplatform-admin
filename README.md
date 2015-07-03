# Performance Platform admin

[![Build status](https://travis-ci.org/alphagov/performanceplatform-admin.svg?branch=master)](https://travis-ci.org/alphagov/performanceplatform-admin)
[![Coverage Status](https://coveralls.io/repos/alphagov/performanceplatform-admin/badge.png)](https://coveralls.io/r/alphagov/performanceplatform-admin)
[![Code Health](https://landscape.io/github/alphagov/performanceplatform-admin/master/landscape.png)](https://landscape.io/github/alphagov/performanceplatform-admin/master)

Performance Platform admin is a [Flask][] app that allows authorised
users to update [performance data on GOV.UK][pp].

[Flask]: http://flask.pocoo.org/
[pp]: https://www.gov.uk/performance

## Application dependencies

We recommend using [virtualenv][] to manage this application's dependencies. If you are using the performance platform development VM, run `workon performanceplatform-admin` to source this.

To set up, run:

```bash
pip install -r requirements.txt
```

[virtualenv]: http://virtualenv.readthedocs.org/

[Redis][] is also required to run the application. It is already on the dev vm. If you prefer to install it locally:

```bash
brew install redis
```

To start run `redis-server`

A good guide to adding redis to launchctl can be found [here][]

[Redis]: http://redis.io/
[here]: http://mac-dev-env.patrickbougie.com/redis/

### Bypassing signon in dev

If you're running this in dev, an additional route '/sign-in' is available to bypass authing with signon.


### Getting set up with GOV.UK's single sign-on service

1. Create a [signon application and user](https://github.com/alphagov/signonotron2#usage)
2. Update [development config](https://github.com/alphagov/performanceplatform-admin/blob/master/admin/config/development.py) with OAuth2 credentials
3. Set an environment variable to allow OAuth over insecure TLS in development: `export OAUTHLIB_INSECURE_TRANSPORT=1`
4. Run the app as normal

### Compiling stylesheets

If you need to compile stylesheets outside of the normal app starting process then run:

```bash
python tools/compile_sass.py
```

## Running the app

```bash
python start.py 3070
```

or if you're using the [Performance Platform development environment](https://github.com/alphagov/pp-puppet) you can

```bash
bowl admin
```

Starting the app in development will automatically compile stylesheets.

You can modify your local configuration without affecting version control using
the instructions in the `admin/config/development.py` file.

## Running tests

```bash
./run_tests.sh
```

## Populating the DB with 'seed' values
Clone the stagecraft repo then from that folder, run:

```
 ./replicate-db.sh postgresql-primary-1.pp-preview
```
