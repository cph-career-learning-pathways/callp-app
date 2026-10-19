#!/bin/bash

# Install CaLLP HTTPS bootstrap and renewal services after deployment.
# Only bootstrap starts initially; renewal starts after HTTPS is verified.

# Stop on unhandled errors, unset variables, or pipeline failures.
set -euo pipefail

SOURCE="/var/app/current/.platform"
DEST="/opt/callp-https"
SYSTEMD="/etc/systemd/system"

# Install the bootstrap script and HTTPS configuration template.
install -d -m 755 "$DEST"
install -m 755 "$SOURCE/scripts/bootstrap_https.sh" "$DEST/bootstrap_https.sh"
install -m 644 "$SOURCE/templates/20_callp_https.conf" "$DEST/20_callp_https.conf"

# Install both bootstrap and renewal systemd units.
for unit in \
    callp-https-bootstrap.service \
    callp-https-bootstrap.timer \
    callp-certbot-renew.service \
    callp-certbot-renew.timer
do
    install -m 644 "$SOURCE/systemd/$unit" "$SYSTEMD/$unit"
done

# Validate the units before enabling the bootstrap timer.
systemd-analyze verify \
    "$SYSTEMD/callp-https-bootstrap.service" \
    "$SYSTEMD/callp-https-bootstrap.timer" \
    "$SYSTEMD/callp-certbot-renew.service" \
    "$SYSTEMD/callp-certbot-renew.timer"

systemctl daemon-reload

# Bootstrap enables renewal after confirming HTTPS is working.
systemctl enable --now callp-https-bootstrap.timer

# Queue an immediate attempt without waiting for DNS or certificate issuance.
# The timer remains active for retries if bootstrap cannot complete yet.
if ! systemctl start --no-block callp-https-bootstrap.service; then
    echo "WARNING: Could not queue HTTPS bootstrap; timer will retry." >&2
fi

echo "CaLLP HTTPS automation installed; bootstrap scheduled."