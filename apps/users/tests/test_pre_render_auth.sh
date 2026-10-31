#!/usr/bin/env bash
# Isolated CI smoke: Nginx must deny protected STATIC HTML before delivery.
# All test users/sessions are fake; this script never reaches production.
set -euo pipefail
cd "$(dirname "$0")/../../.."

python3 -u apps/users/tests/mock_identity_for_nginx.py &
mock_pid=$!
cleanup() {
  docker rm -f qp-auth-guard-nginx >/dev/null 2>&1 || true
  kill "$mock_pid" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run -d --name qp-auth-guard-nginx \
  --add-host quantum-platform-user-api.quantum-platform.svc.cluster.local:host-gateway \
  -p 127.0.0.1:18080:8080 \
  -v "$PWD/apps/users/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
  -v "$PWD/apps/users/dist:/usr/share/nginx/html:ro" \
  nginxinc/nginx-unprivileged:1.29-alpine >/dev/null

for i in $(seq 1 15); do
  if curl -fsS http://127.0.0.1:18080/healthz >/dev/null 2>&1; then break; fi
  sleep 1
done

body=$(mktemp)
trap 'rm -f "$body"; cleanup' EXIT
check() {
  local expected="$1" path="$2" cookie="${3:-}"
  local result
  if [[ -n "$cookie" ]]; then
    result=$(curl -sS -o "$body" -w '%{http_code}' \
      -H "Cookie: $cookie" "http://127.0.0.1:18080$path")
  else
    result=$(curl -sS -o "$body" -w '%{http_code}' "http://127.0.0.1:18080$path")
  fi
  if [[ "$result" != "$expected" ]]; then
    echo "::error::HTTP $path expected $expected got $result"
    exit 1
  fi
  if [[ "$expected" == 302 ]] && grep -q 'Research profile' "$body"; then
    echo "::error::Protected HTML disclosed on $path"
    exit 1
  fi
  echo "Verified $path -> $result"
}

check 200 /
check 200 /login/
check 200 /account/signup/
check 302 /profile/
check 302 /profile/index.html
check 302 /programmes/
check 302 /security/
check 302 /dashboard/
check 302 /agent/
check 302 /runs/
check 302 /workbench/
check 302 /account/access-keys/
check 302 /account/mfa/settings/
check 302 /access/

check 200 /profile/ 'sessionid=valid'
if ! grep -q 'Research profile' "$body"; then
  echo "::error::Authorized profile HTML missing"
  exit 1
fi
check 200 /programmes/ 'sessionid=valid'

# Identity-service outage must fail CLOSED, not serve static private HTML.
kill "$mock_pid"
wait "$mock_pid" 2>/dev/null || true
sleep 1
response=$(curl -sS -o "$body" -w '%{http_code}' http://127.0.0.1:18080/profile/)
if [[ "$response" == 200 ]] || grep -q 'Research profile' "$body"; then
  echo "::error::Authentication backend failure revealed protected HTML"
  exit 1
fi
echo "Verified fail-closed on identity backend outage ($response)"
