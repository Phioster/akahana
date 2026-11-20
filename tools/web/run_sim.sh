#!/usr/bin/env bash
# The browser test (?probe) in Apple's iOS simulator, real Mobile Safari: the newest iPhone and iPad there.
# Usage: run_sim.sh <base url> <logs dir> <shots dir>
set -uo pipefail
BASE=$1 LOGS=$2 SHOTS=$3
mkdir -p "$SHOTS"
xcrun simctl list devices available -j > /tmp/sims.json
pick() {   # newest runtime's first device whose name starts with $1
	python3 - "$1" <<'E'
import json, sys, re
d = json.load(open('/tmp/sims.json'))['devices']
ios = sorted((k for k in d if 'iOS' in k), key=lambda k: [int(x) for x in re.findall(r'\d+', k)], reverse=True)
for k in ios:
    for dev in d[k]:
        if dev['name'].startswith(sys.argv[1]):
            print(dev['udid'], dev['name'].replace(' ', '_'), k.split('.')[-1]); sys.exit()
E
}
done_in() { [ -f "$LOGS/$1.jsonl" ] && grep -q 'kind\\": \\"done\|kind\\":\\"done' "$LOGS/$1.jsonl"; }
for kind in ${SIM_KINDS:-iPhone iPad}; do
	read -r UDID NAME RT <<< "$(pick "$kind")"
	[ -z "${UDID:-}" ] && { echo "kein $kind-Simulator"; continue; }
	xcrun simctl boot "$UDID" 2>/dev/null
	xcrun simctl bootstatus "$UDID" -b > /dev/null
	sleep 20                                  # Safari's first start settles
	for V in ${SIM_VARIANTS:-normal}; do      # e.g. "normal noreflect stay dpr=1": one run each
	DEV="sim-$NAME-${V//=/}"
	echo "$DEV ($RT)"
	xcrun simctl openurl "$UDID" "$BASE/index.html?probe&dev=$DEV&$V"
	n=0; start=$SECONDS
	while (( SECONDS - start < 420 )) && ! done_in "$DEV"; do
		sleep 15
		xcrun simctl io "$UDID" screenshot "$SHOTS/${DEV}_$(printf %02d $n).png" > /dev/null 2>&1; n=$((n+1))
	done
	xcrun simctl io "$UDID" screenshot "$SHOTS/${DEV}_ende.png" > /dev/null 2>&1
	if done_in "$DEV"; then echo "$DEV fertig in $((SECONDS - start)) s"; else echo "$DEV NICHT fertig"; fi
	xcrun simctl terminate "$UDID" com.apple.mobilesafari 2>/dev/null; sleep 3
	done
	xcrun simctl shutdown "$UDID"
done
exit 0
