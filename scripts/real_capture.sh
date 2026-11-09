#!/usr/bin/env bash
# Real on-disk BLACKSPOT demo on Linux loop devices — genuine kernel block-layer
# behaviour, no physical drive and no risk to any real disk.
#
# It shows the two verdicts that matter, each from REAL kernel behaviour:
#   1) ALIVE   — a file is deleted but NOT trimmed; its bytes persist in the raw
#                device, so BLACKSPOT reads them back (host-side recovery is real).
#   2) LYING   — a real `blkdiscard` (the discard/TRIM ioctl) is issued; reads now
#                return deterministic zeros (DZAT). On a real SSD those zeros can
#                mask live NAND — which is exactly the verdict BLACKSPOT raises.
#
# Requires root (losetup/mkfs/mount/blkdiscard). Operates only on its own images.
# Usage: sudo scripts/real_capture.sh [workdir]
set -euo pipefail

WORK="${1:-/tmp/blackspot_real}"
SRC="$(cd "$(dirname "$0")/.." && pwd)/src"
MAGIC="BLACKSPOT-TREASURE-XMARKSTHESPOT"
rm -rf "$WORK"; mkdir -p "$WORK"
LOOPS=()
cleanup() {
  for m in "$WORK"/mnt_*; do mountpoint -q "$m" 2>/dev/null && umount "$m" || true; done
  for l in "${LOOPS[@]:-}"; do losetup -d "$l" 2>/dev/null || true; done
}
trap cleanup EXIT

make_loop() {  # $1=name  -> echoes loop device
  local img="$WORK/$1.img"
  dd if=/dev/zero of="$img" bs=1M count=64 status=none
  local loop; loop="$(losetup --find --show "$img")"
  LOOPS+=("$loop")
  mkfs.ext4 -q -F "$loop"
  echo "$loop"
}

write_canary() {  # $1=loop $2=mnt
  mkdir -p "$2"; mount "$1" "$2"
  python3 - "$2/treasure.txt" "$MAGIC" <<'PY'
import sys
open(sys.argv[1], "wb").write((sys.argv[2] + "\n").encode() * 4096)
PY
  sync
}

find_lbas() {  # $1=loop  -> echoes "lba0,lba1,.."
  local off lba
  off="$(grep -a -b -o -m1 "$MAGIC" "$1" | head -1 | cut -d: -f1)"
  off="${off:-0}"; lba=$((off / 512))
  echo "$lba,$((lba+8)),$((lba+16)),$((lba+24))"
}

triage() {  # $1=loop $2=lbas $3=extra-flags...
  shift 2 2>/dev/null || true
  :
}

echo "########################################################"
echo "# Scenario 1: deleted but NOT trimmed  -> expect ALIVE #"
echo "########################################################"
L1="$(make_loop alive)"; echo "  loop: $L1"
write_canary "$L1" "$WORK/mnt_alive"
LBAS1="$(find_lbas "$L1")"; echo "  canary LBAs: $LBAS1"
rm -f "$WORK/mnt_alive/treasure.txt"; sync        # delete, but do NOT trim
echo "  raw bytes after delete: $(dd if="$L1" bs=512 skip="${LBAS1%%,*}" count=1 2>/dev/null | tr -d '\0' | head -c 40)"
PYTHONPATH="$SRC" python3 -m blackspot.capture capture --target "$L1" \
  --attempts 3 --quiesce 0 --lbas "$LBAS1" \
  --model "LoopDemo" --controller "kernel-loop" --out "$WORK/alive.json" >/dev/null
PYTHONPATH="$SRC" python3 -m blackspot.cli triage --capture "$WORK/alive.json"

echo
echo "#############################################################"
echo "# Scenario 2: real blkdiscard (TRIM ioctl) -> expect LYING  #"
echo "#############################################################"
L2="$(make_loop scuttled)"; echo "  loop: $L2"
write_canary "$L2" "$WORK/mnt_scuttled"
LBAS2="$(find_lbas "$L2")"; echo "  canary LBAs: $LBAS2"
rm -f "$WORK/mnt_scuttled/treasure.txt"; sync
umount "$WORK/mnt_scuttled"
echo "  issuing real blkdiscard on $L2 ..."
blkdiscard -f "$L2" || echo "  (blkdiscard unsupported on this loop; see notes)"
sync
echo "  raw bytes after discard: '$(dd if="$L2" bs=512 skip="${LBAS2%%,*}" count=1 2>/dev/null | tr -d '\0' | head -c 40)'"
PYTHONPATH="$SRC" python3 -m blackspot.capture capture --target "$L2" \
  --attempts 3 --quiesce 0 --lbas "$LBAS2" --idle 30 \
  --model "LoopDemo" --controller "kernel-loop(discard)" --out "$WORK/scuttled.json" >/dev/null
PYTHONPATH="$SRC" python3 -m blackspot.cli triage --capture "$WORK/scuttled.json"

echo
echo "[*] done. captures in $WORK/{alive,scuttled}.json"
