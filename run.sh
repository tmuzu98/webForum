#!/bin/sh

export FLASK_APP=app.py
export FLASK_ENV=development

exec flask run
