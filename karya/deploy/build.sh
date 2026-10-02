#!/usr/bin/env bash
# Build Karya images on the deploy box (arm64). Run from the repo root:  karya/deploy/build.sh 1.4.2-k1
# Images: karya-web, karya-admin, karya-space, karya-backend (api/worker/beat/migrator), karya-live.
# The proxy (Caddy) is unmodified and stays makeplane/plane-proxy.
set -euo pipefail
TAG=${1:?usage: build.sh <tag>}
cd "$(git rev-parse --show-toplevel)"
python3 karya/rebrand.py --check   # refuse to build an un-rebranded tree
build() { echo "=== $1 $(date -u +%T)"; docker buildx build --load -f "$2" -t "karya-$1:$TAG" "${3:-.}"; }
build web     apps/web/Dockerfile.web
build admin   apps/admin/Dockerfile.admin
build space   apps/space/Dockerfile.space
build live    apps/live/Dockerfile.live
build backend apps/api/Dockerfile.api apps/api
echo "=== done $(date -u +%T)"; docker images "karya-*" --format '{{.Repository}}:{{.Tag}} {{.Size}}'
