#!/bin/bash
# Restore and verify HTTPS immediately after an EB configuration deployment.
set -euo pipefail

SERVICE="callp-https-bootstrap.service"

if ! systemctl is-enabled --quiet callp-https-bootstrap.timer; then
    echo "ERROR: CaLLP HTTPS bootstrap timer is not installed/enabled." >&2
    exit 1
fi

# Blocking start: the existing service validates the certificate and listener.
# Its retry timer remains responsible for later recovery if this attempt fails.
systemctl start "$SERVICE"
echo "CaLLP HTTPS bootstrap completed after configuration deployment."