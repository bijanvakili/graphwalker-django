# Example: Sentry

### Introduction

This step by step guide will show you how to export the Django models
in [Sentry](https://sentry.io/welcome/) to graphwalker JSON format.
 
NOTE: This is broken due to compatability issues between Sentry (on Django 1.6) and django-extensions
(which no longer supports Django 1.6)
 
### Instructions

1. Setup local Postgres database


    createdb -E utf-8 sentry

2. Setup Redis (TBD)


    docker run --detach --name sentry-redis --publish 6379:6379 redis:3.2-alpine

3. Setup Sentry by following the [Installation with Python](https://docs.sentry.io/server/installation/python/) instructions

Install python dependencies:

    pyenv install 2.7.13
    pyenv virtualenv 2.7.13 sentry
    pyenv local sentry
    pip install -U pip
    pip install -U setuptools
    pip install -U sentry
    
    # workaround to use redis client v2.10.5
    # see https://github.com/getsentry/sentry/pull/5905
    pip uninstall redis
    pip install redis==2.10.5

Initialize Sentry configuration with a local directory:

    mkdir -p ./etc/sentry
    sentry init ./etc/sentry

Edit `./etc/sentry/sentry.conf.py` to:
* set `DATABASES` as necessary.
* add django extensions to installed apps

```python
INSTALLED_APPS = INSTALLED_APPS + ('django_extensions',)
```

4. Install `pygraphviz`


    pip install pygraphviz

5. Install [django-extensions](https://github.com/django-extensions/django-extensions)

```bash
pip install git+https://github.com/django-extensions/django-extensions.git@8bb0f74e7db4601e8af3340bd9423c4fe9eb5722
```

Change line 103 in `django_extensions/management/modelviz.py` from:

```python
appmodels = list(get_models_compat(app_label))
```

to:

```python
appmodels = list(get_models_compat(app))
```

6. Run the database migrations:

    SENTRY_CONF=./etc/sentry sentry upgrade

7. Export the models to `django-extensions` JSON format.

This uses the [graph_models](https://django-extensions.readthedocs.io/en/latest/graph_models.html) command

    SENTRY_CONF=./etc/sentry sentry django graph_models --json -o output.json sentry

NOTE:
This will crash, but you can see the entire JSON output in stdout.
* Copy it to a file
* Fix quotes, boolean and null types
* Key the main content under:

```json
"graphs" : [
    ...
    {...}
]
```

### TODO

* Update to use _only_ Docker installation instructions via `docker-compose`
* Update if `graphwalker-django` becomes a standalone package
