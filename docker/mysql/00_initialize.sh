#!/bin/sh
set -eu

SQL_DIR="/docker-entrypoint-initdb.d/sql"
cd "$SQL_DIR"

# Create a temporary MySQL client configuration file.
MYSQL_CNF="$(mktemp)"

cleanup() {
    rm -f "$MYSQL_CNF"
}
trap cleanup EXIT

chmod 600 "$MYSQL_CNF"

printf '[client]\nuser=root\npassword=%s\n' \
    "$MYSQL_ROOT_PASSWORD" > "$MYSQL_CNF"

run_mysql() {
    mysql \
        --defaults-extra-file="$MYSQL_CNF" \
        --default-character-set=utf8mb4 \
        --protocol=socket \
        "$MYSQL_DATABASE"
}

# Initialize schema, triggers, and reserved accounts.
for file in \
    01_schema_setup.sql \
    02_triggers.sql \
    03_seed_reserved_accounts.sql
do
    echo "Initializing: $file"
    run_mysql < "$file"
done

# Populate reference and sample data.
echo "Initializing: 05_populate.sql"

sed '/^[[:space:]]*source[[:space:]]/Id' \
    05_populate.sql | run_mysql

# Create views.
echo "Initializing: 04_views.sql"
run_mysql < 04_views.sql

echo "CaLLP local MySQL initialization completed."