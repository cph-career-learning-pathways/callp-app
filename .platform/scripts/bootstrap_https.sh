#!/bin/bash
set -euo pipefail

# Initialize or restore CaLLP HTTPS after deployment or EC2 replacement.
# Elastic Beanstalk manages the Elastic IP; certificate renewal starts
# only after HTTPS is verified.

DOMAIN="callp.dev"
CERTBOT="/opt/callp-certbot/bin/certbot"
WEBROOT="/var/www/callp-acme"
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
TEMPLATE="/opt/callp-https/20_callp_https.conf"
ACTIVE="/etc/nginx/conf.d/20_callp_https.conf"
LOCK="/run/lock/callp-https-bootstrap.lock"
CA_BUNDLE="/etc/pki/tls/certs/ca-bundle.crt"

log() { printf '[callp-https] %s\n' "$*"; }
fail() { log "ERROR: $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "Run as root"
for command_name in curl getent awk sort openssl nginx systemctl flock mktemp install cmp cp rm chmod sha256sum timeout; do
    command -v "$command_name" >/dev/null 2>&1 || fail "Missing command: $command_name"
done
[ -x "$CERTBOT" ] || fail "Certbot is not installed"
[ -r "$TEMPLATE" ] || fail "HTTPS template is missing"
[ -d "$WEBROOT" ] || fail "ACME webroot is missing"
[ -r "$CA_BUNDLE" ] || fail "System CA bundle is missing"

# Prevent overlapping timer and manual invocations.
exec 9>"$LOCK"
flock -n 9 || fail "Another bootstrap is running"

certificate_valid() {
    local cert="$CERT_DIR/cert.pem"
    local key="$CERT_DIR/privkey.pem"
    local certificate_public_key private_public_key

    [ -s "$cert" ] && [ -s "$CERT_DIR/fullchain.pem" ] && [ -s "$key" ] || return 1
    openssl x509 -in "$cert" -noout -checkend 0 >/dev/null 2>&1 || return 1
    openssl verify -CAfile "$CA_BUNDLE" -untrusted "$CERT_DIR/fullchain.pem" \
        -verify_hostname "$DOMAIN" "$cert" >/dev/null 2>&1 || return 1

    # Compare public keys without displaying or copying the private key.
    certificate_public_key=$(openssl x509 -in "$cert" -pubkey -noout 2>/dev/null |
        openssl pkey -pubin -outform DER 2>/dev/null | sha256sum) || return 1
    private_public_key=$(openssl pkey -in "$key" -pubout -outform DER 2>/dev/null |
        sha256sum) || return 1
    [ "$certificate_public_key" = "$private_public_key" ]
}

served_certificate_matches() {
    local expected served
    expected=$(openssl x509 -in "$CERT_DIR/cert.pem" -outform DER 2>/dev/null |
        sha256sum) || return 1
    served=$(timeout 10 openssl s_client -connect 127.0.0.1:443 \
        -servername "$DOMAIN" </dev/null 2>/dev/null |
        openssl x509 -outform DER 2>/dev/null | sha256sum) || return 1
    [ "$expected" = "$served" ]
}

check_http_challenge() {
    local token instance_ip domain_ips challenge_dir probe url response
    token=$(curl --noproxy '*' -fsS --max-time 5 -X PUT \
        -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' \
        http://169.254.169.254/latest/api/token) || fail "IMDSv2 unavailable"
    instance_ip=$(curl --noproxy '*' -fsS --max-time 5 \
        -H "X-aws-ec2-metadata-token: $token" \
        http://169.254.169.254/latest/meta-data/public-ipv4) || fail "Public IP unavailable"
    domain_ips=$(getent ahostsv4 "$DOMAIN" | awk '{print $1}' | sort -u) || fail "DNS lookup failed"
    [ "$domain_ips" = "$instance_ip" ] || fail "DNS does not match this instance; retry later"

    challenge_dir="$WEBROOT/.well-known/acme-challenge"
    install -d -m 755 "$challenge_dir"
    probe=$(mktemp "$challenge_dir/callp-probe.XXXXXXXX")
    trap 'rm -f "${probe:-}"' EXIT
    chmod 644 "$probe"
    printf 'callp-bootstrap-check\n' >"$probe"
    url="http://$DOMAIN/.well-known/acme-challenge/${probe##*/}"

    response=$(curl --noproxy '*' -fsS --max-time 10 \
        --resolve "$DOMAIN:80:127.0.0.1" "$url") || fail "Local challenge route failed"
    [ "$response" = 'callp-bootstrap-check' ] || fail "Local challenge content mismatch"
    response=$(curl --noproxy '*' -fsS --max-time 10 "$url") || fail "Public challenge route failed"
    [ "$response" = 'callp-bootstrap-check' ] || fail "Public challenge content mismatch"
    rm -f "$probe"
    trap - EXIT
}

# Reuse trusted certificates. Never silently overwrite an invalid lineage.
if ! certificate_valid; then
    if [ -e "$CERT_DIR/cert.pem" ] || [ -e "$CERT_DIR/fullchain.pem" ]; then
        fail "Existing certificate is invalid or untrusted; investigate"
    fi
    check_http_challenge
    log "Requesting production certificate"
    "$CERTBOT" certonly --webroot -w "$WEBROOT" -d "$DOMAIN" \
        --cert-name "$DOMAIN" --non-interactive --agree-tos \
        --register-unsafely-without-email || fail "Certificate issuance failed"
    certificate_valid || fail "Issued certificate failed verification"
fi

# Start renewal only after HTTPS is confirmed working.
enable_renewal() {
    systemctl enable --now callp-certbot-renew.timer || fail "Could not enable certificate renewal timer"
}

# Even unchanged configuration may need a reload after certificate issuance.
if [ -f "$ACTIVE" ] && cmp -s "$TEMPLATE" "$ACTIVE"; then
    nginx -t || fail "Existing Nginx configuration is invalid"
    if served_certificate_matches; then
        enable_renewal
        log "HTTPS already active with the expected certificate"
        exit 0
    fi
    if ! systemctl reload nginx || ! served_certificate_matches; then
        # The existing file was not changed; restoring it cannot repair a
        # failed listener. Leave it untouched for investigation/retry.
        fail "Existing HTTPS listener could not be restored; configuration unchanged"
    fi
    enable_renewal
    log "HTTPS listener reloaded successfully"
    exit 0
fi

# Back up an existing configuration before changing it.
backup=''
if [ -e "$ACTIVE" ]; then
    backup=$(mktemp /etc/nginx/conf.d/.callp-https-backup.XXXXXXXX)
    cp -p "$ACTIVE" "$backup"
fi

restore_config() {
    if [ -n "$backup" ] && [ -f "$backup" ]; then
        cp -p "$backup" "$ACTIVE"
        rm -f "$backup"
    else
        rm -f "$ACTIVE"
    fi
    if nginx -t >/dev/null 2>&1; then
        systemctl reload nginx || log "WARNING: Nginx rollback reload failed"
    else
        log "WARNING: Restored Nginx configuration did not validate"
    fi
}

install -m 644 "$TEMPLATE" "$ACTIVE"
if ! nginx -t || ! systemctl reload nginx || ! served_certificate_matches; then
    restore_config
    fail "HTTPS activation failed; previous configuration restored where possible"
fi
[ -z "$backup" ] || rm -f "$backup"
enable_renewal
log "HTTPS activated and serving the verified certificate"
