#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Compile static files and run migrations inside django_backend
python django_backend/manage.py collectstatic --no-input
python django_backend/manage.py migrate
