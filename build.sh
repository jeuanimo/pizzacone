#!/bin/bash

# Exit on any error
set -o errexit

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
