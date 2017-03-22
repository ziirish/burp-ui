#!/bin/ash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE USER burpui PASSWORD 'burpui';
        CREATE DATABASE burpuidb;
        GRANT ALL PRIVILEGES ON DATABASE burpuidb TO burpui;
EOSQL
