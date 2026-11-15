#!/usr/bin/env bash
# Baut die APK in der CI (vom Standard-Branch), laedt sie, signiert sie mit dem lokalen Schluessel und installiert sie.
set -uo pipefail
cd "$(dirname "$0")/.."
gh workflow run build.yml --ref master || exit 1
sleep 8
ID=$(gh run list --workflow=build.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$ID" --exit-status > /dev/null 2>&1 || { gh run view "$ID" --log-failed | tail -40; exit 1; }
gh run list --workflow=test.yml --limit 1
for try in 1 2 3; do                      # the download sometimes drops on mobile data
	# die CI haengt die APK ans Release "dev" (keine Artefakte mehr: 1 Tag Aufbewahrung)
	rm -rf apk && mkdir -p apk/dev && gh release download dev -p mohnweg-debug.apk -D apk/dev --clobber && break
	[ "$try" = 3 ] && { echo "APK nicht geladen"; exit 1; }
done
bash tools/sign.sh apk/*/mohnweg-debug.apk --install
