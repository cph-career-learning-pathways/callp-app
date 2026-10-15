#!/bin/bash
set -euo pipefail

# Install Python 3.11 without changing the system Python.
dnf install -y python3.11 python3.11-pip

# Create an isolated environment for Certbot.
if [ ! -x /opt/callp-certbot/bin/python ]; then
    python3.11 -m venv /opt/callp-certbot
fi

# Install the versions verified on CaLLP's EC2 instance.
/opt/callp-certbot/bin/python -m pip install \
    "pip==26.2.1"

/opt/callp-certbot/bin/python -m pip install \
    "certbot==5.8.0"

# Create the HTTP-01 challenge directory.
install -d -m 755 \
    /var/www/callp-acme/.well-known/acme-challenge

echo "CaLLP Certbot installation completed."
