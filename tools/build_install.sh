#!/usr/bin/env bash
# Baut die APK in der CI (vom Standard-Branch), laedt sie, signiert sie mit dem lokalen Schluessel und installiert sie.
set -uo pipefail
cd "$(dirname "$0")/.."
gh workflow run build.yml --ref master || exit 1
sleep 8
ID=$(gh run list --workflow=build.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$ID" --exit-status > /dev/null 2>&1 || { gh run view "$ID" --log-failed | tail -40; exit 1; }
gh run list --workflow=test.yml --limit 1
rm -rf apk && mkdir -p apk && gh run download "$ID" -D apk || exit 1
bash tools/sign.sh apk/*/mohnweg-debug.apk --install
