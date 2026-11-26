#!/bin/sh
# Install the modules into a fresh database and run their tests.
# Usage: tools/test-in-docker.sh <odoo-major-version> [addons-dir]
# Needs Docker only. Creates containers/network prefixed "test-odoo-" and removes them again
# unless KEEP=1 is set (then the database container stays for a UI check).
set -eu
V="${1:?odoo version, e.g. 18}"
ADDONS="$(cd "${2:-$(dirname "$0")/..}" && pwd)"
NET=test-odoo-net
PG=test-odoo-pg-$V
LIMITS="--cpus 4 --memory 8g"
# throwaway database password, generated per run (never stored)
PGPW="$(od -An -N12 -tx1 /dev/urandom | tr -d ' [:space:]')"
docker network inspect $NET >/dev/null 2>&1 || docker network create $NET >/dev/null
docker rm -f $PG >/dev/null 2>&1 || true
docker volume rm test-odoo-data-$V >/dev/null 2>&1 || true
docker run -d --name $PG --network $NET $LIMITS -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD="$PGPW" \
  -e POSTGRES_DB=postgres "${PGIMAGE:-postgres:16}" >/dev/null
# needed to attach a web container to the kept database
if [ "${KEEP:-0}" = 1 ]; then echo "PGPW=$PGPW"; fi
until docker exec $PG pg_isready -U odoo >/dev/null 2>&1; do sleep 1; done
sleep 2
MODS=delegaize_connector,delegaize_connector_crm,delegaize_connector_sale,delegaize_connector_account
docker run --rm --name test-odoo-$V --network $NET $LIMITS \
  -e HOST=$PG -e USER=odoo -e PASSWORD="$PGPW" \
  -v test-odoo-data-$V:/var/lib/odoo -v "$ADDONS":/mnt/extra-addons:ro "odoo:$V" \
  odoo -d "test$V" -i "crm,sale_management,account,$MODS" --load-language=en_US,de_DE \
  --test-tags "/delegaize_connector,/delegaize_connector_crm,/delegaize_connector_sale,/delegaize_connector_account" \
  --stop-after-init --log-level=test > "test-$V.log" 2>&1 || true
grep -E "ERROR|FAIL|Traceback|tests when loading|Ran [0-9]+ test|failed, " "test-$V.log" | tail -40 || true
echo "== installed modules (v$V) =="
docker exec $PG psql -U odoo -d "test$V" -tAc \
  "select name||' '||state||' '||coalesce(latest_version,'') from ir_module_module where name like 'delegaize%' order by name"
if [ "${KEEP:-0}" != 1 ]; then docker rm -f $PG >/dev/null; docker volume rm test-odoo-data-$V >/dev/null; fi
