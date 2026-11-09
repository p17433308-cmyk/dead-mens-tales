#!/usr/bin/env bash
# Real TRIM/discard canary demo on a Linux loopback device.
# No physical drive is touched; everything happens inside a file-backed image.
# Demonstrates the actual block-layer TRIM -> read behaviour end-to-end.
#
# Requires root (losetup/mkfs/mount/fstrim). Safe: operates only on $IMG.
#
# Usage:  sudo scripts/loop_canary.sh [workdir]
set -euo pipefail

WORK="${1:-/tmp/blackspot_canary}"
IMG="$WORK/canary.img"
MNT="$WORK/mnt"
REPO_SRC="$(cd "$(dirname "$0")/.." && pwd)/src"

echo "[*] workspace: $WORK"
rm -rf "$WORK"; mkdir -p "$MNT"

echo "[*] creating 64 MiB image + loop device (with discard)"
dd if=/dev/zero of="$IMG" bs=1M count=64 status=none
LOOP="$(losetup --find --show "$IMG")"
trap 'umount "$MNT" 2>/dev/null || true; losetup -d "$LOOP" 2>/dev/null || true' EXIT
echo "    loop = $LOOP"

echo "[*] mkfs.ext4 + mount -o discard"
mkfs.ext4 -q -F "$LOOP"
mount -o discard "$LOOP" "$MNT"

echo "[*] writing canary file (the 'treasure')"
CANARY="$MNT/treasure.txt"
python3 - "$CANARY" <<'PY'
import sys
# A recognizable, low-entropy canary so recovery is visually obvious.
open(sys.argv[1], "wb").write(b"BLACKSPOT-CANARY-XMARKSTHESPOT\n" * 4096)
PY
sync
echo "    canary size: $(stat -c%s "$CANARY") bytes"

# Locate the canary by searching the RAW device for its magic string — the most
# robust way to find exactly where the data physically lives on the medium.
OFF="$(grep -a -b -o -m1 'BLACKSPOT-CANARY' "$LOOP" | head -1 | cut -d: -f1)"
if [ -z "${OFF:-}" ]; then echo "    canary magic not found on device"; OFF=0; fi
START_LBA=$((OFF / 512))
LBAS="$START_LBA,$((START_LBA+8)),$((START_LBA+16)),$((START_LBA+24))"
echo "    found canary magic at byte $OFF -> physical LBA $START_LBA (LBAs $LBAS)"

echo "[*] CAPTURE BEFORE delete (read-only) — expect the treasure to be present"
PYTHONPATH="$REPO_SRC" python3 -m blackspot.capture capture \
  --target "$LOOP" --attempts 3 --quiesce 0 \
  --model "LoopDemo" --controller "kernel-loop(discard)" \
  --lbas "$LBAS" --out "$WORK/before.json" >/dev/null
PYTHONPATH="$REPO_SRC" python3 -m blackspot.cli triage --capture "$WORK/before.json"
echo "    bytes at canary LBA (before): $(dd if="$LOOP" bs=512 skip="$START_LBA" count=1 2>/dev/null | tr -d '\0' | head -c 48)"

echo "[*] deleting canary + issuing real fstrim"
rm -f "$CANARY"
sync
fstrim -v "$MNT" || echo "    (fstrim reported nothing; kernel/loop may batch discard)"
sync; sleep 1

echo "[*] CAPTURE AFTER delete+TRIM (read-only) — treasure should be gone/masked"
PYTHONPATH="$REPO_SRC" python3 -m blackspot.capture capture \
  --target "$LOOP" --attempts 3 --quiesce 0 \
  --model "LoopDemo" --controller "kernel-loop(discard)" \
  --lbas "$LBAS" --idle 1 --out "$WORK/after.json" >/dev/null
PYTHONPATH="$REPO_SRC" python3 -m blackspot.cli triage --capture "$WORK/after.json"
echo "    bytes at canary LBA (after):  $(dd if="$LOOP" bs=512 skip="$START_LBA" count=1 2>/dev/null | tr -d '\0' | head -c 48)"

echo "[*] examiner report (after state):"
PYTHONPATH="$REPO_SRC" python3 -m blackspot.cli report \
  --capture "$WORK/after.json" --case-id DEMO-001 \
  --examiner "BLACKSPOT demo" --exhibit "$LOOP" --out "$WORK/report.md"
echo "    -> $WORK/report.md"
echo "[*] done."
