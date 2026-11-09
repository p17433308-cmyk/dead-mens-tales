"""BLACKSPOT capture harness — produce reproducible read maps from a device.

Safety model (read this):
  * The default mode is strictly READ-ONLY. It opens the target, reads the same
    LBA ranges several times, hashes each read, and records whether it was all
    zero. It never writes.
  * `--simulate PATH` runs against a file-backed image instead of a real device,
    so you can build and test the whole pipeline with NO hardware and NO risk.
  * Issuing TRIM is DESTRUCTIVE and is deliberately NOT done here. A separate,
    heavily-guarded `trim` subcommand exists and refuses to run unless you pass
    the exact device path AND the confirmation token. Never point it at a drive
    whose data you need.

Output is a capture JSON consumable by `blackspot triage`.

Platform notes:
  * Linux / WSL: target is a block device like /dev/sdb or an image file.
  * Windows: run under WSL, or read \\\\.\\PhysicalDriveN from an elevated shell
    (raw physical reads need Administrator).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter

SECTOR = 512
DEFAULT_SPAN = 4096  # bytes read per LBA sample


def _shannon_entropy(data: bytes) -> float:
    """Bits per byte (0..8)."""
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return round(-sum((c / n) * math.log2(c / n) for c in counts.values()), 3)


def _nonzero_fraction(data: bytes) -> float:
    if not data:
        return 0.0
    return round(1.0 - (data.count(0) / len(data)), 4)


def _read_at(fd: int, offset: int, length: int) -> bytes:
    os.lseek(fd, offset, os.SEEK_SET)
    buf = b""
    while len(buf) < length:
        chunk = os.read(fd, length - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf


def sample(path: str, lbas: list[int], attempts: int, span: int,
           quiesce: float) -> list[dict]:
    """Read each LBA `attempts` times (read-only). Returns ReadSample dicts."""
    reads: list[dict] = []
    fd = os.open(path, os.O_RDONLY)
    try:
        for attempt in range(1, attempts + 1):
            for lba in lbas:
                data = _read_at(fd, lba * SECTOR, span)
                reads.append({
                    "lba": lba,
                    "attempt": attempt,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "all_zero": (data.count(0) == len(data) and len(data) > 0),
                    "timestamp": round(time.time(), 3),
                    "nonzero_fraction": _nonzero_fraction(data),
                    "shannon_entropy": _shannon_entropy(data),
                })
            if quiesce and attempt < attempts:
                time.sleep(quiesce)
    finally:
        os.close(fd)
    return reads


def make_sim_image(path: str, size_mb: int, pattern: bytes) -> None:
    """Create a file-backed test image filled with a known pattern (safe)."""
    with open(path, "wb") as fh:
        block = (pattern * (1024 * 1024 // max(len(pattern), 1) + 1))[:1024 * 1024]
        for _ in range(size_mb):
            fh.write(block)


def cmd_capture(args) -> int:
    lbas = [int(x) for x in args.lbas.split(",")] if args.lbas else [100, 204, 512, 1000]
    reads = sample(args.target, lbas, args.attempts, args.span, args.quiesce)
    out = {
        "drive": {
            "model": args.model,
            "controller_family": args.controller,
            "is_sed": args.sed,
            "crypto_erase_confirmed": False,
            "trim_enabled": not args.no_trim,
            "powered_down_since_trim": args.power_cut,
            "idle_seconds_since_delete": args.idle,
            "firmware_claims_zero": all(r["all_zero"] for r in reads) if reads else False,
        },
        "reads": reads,
    }
    text = json.dumps(out, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {len(reads)} read samples -> {args.out}")
    else:
        print(text)
    return 0


def cmd_simulate(args) -> int:
    """Build a file-backed image, then capture from it — fully offline/safe."""
    pattern = b"\x00" * 64 if args.zero else bytes.fromhex("deadbeefcafef00d") * 8
    make_sim_image(args.image, args.size_mb, pattern)
    print(f"created {args.size_mb} MiB simulated image at {args.image} "
          f"({'zeroed' if args.zero else 'patterned'})")
    ns = argparse.Namespace(
        target=args.image, lbas=args.lbas, attempts=args.attempts, span=args.span,
        quiesce=0.0, model=args.model, controller=args.controller, sed=False,
        no_trim=False, power_cut=False, idle=args.idle, out=args.out,
    )
    return cmd_capture(ns)


def cmd_trim(args) -> int:
    """DESTRUCTIVE. Guarded. Issues discard/TRIM to a device you own."""
    token = "I-OWN-THIS-DRIVE"
    if args.confirm != token or args.device != args.confirm_device:
        print("REFUSED. This erases data. To proceed you must pass:")
        print(f"  --device <dev> --confirm {token} --confirm-device <same dev>")
        return 2
    try:
        import subprocess
        # blkdiscard zeroes/trims the whole device (Linux). Explicit and loud.
        print(f"[DESTRUCTIVE] running: blkdiscard -v {args.device}")
        subprocess.run(["blkdiscard", "-v", args.device], check=True)
    except Exception as exc:  # noqa: BLE001
        print(f"trim failed: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="blackspot-capture", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp):
        sp.add_argument("--lbas", default="", help="comma-separated LBAs (default sample set)")
        sp.add_argument("--attempts", type=int, default=3, help="reads per LBA (>=2 to judge determinism)")
        sp.add_argument("--span", type=int, default=DEFAULT_SPAN, help="bytes per read")
        sp.add_argument("--model", default="unknown")
        sp.add_argument("--controller", default="unknown")
        sp.add_argument("--idle", type=float, default=None, help="idle seconds since delete")
        sp.add_argument("--out", default="", help="write JSON here instead of stdout")

    c = sub.add_parser("capture", help="READ-ONLY capture from a device or image")
    add_common(c)
    c.add_argument("--target", required=True, help="block device (/dev/sdb) or image file")
    c.add_argument("--quiesce", type=float, default=2.0, help="seconds between attempts")
    c.add_argument("--sed", action="store_true")
    c.add_argument("--no-trim", action="store_true")
    c.add_argument("--power-cut", action="store_true")
    c.set_defaults(func=cmd_capture)

    s = sub.add_parser("simulate", help="build a file-backed image and capture from it (safe)")
    add_common(s)
    s.add_argument("--image", default="/tmp/blackspot_sim.img")
    s.add_argument("--size-mb", type=int, default=8)
    s.add_argument("--zero", action="store_true", help="fill with zeros (emulate DZAT)")
    s.set_defaults(func=cmd_simulate)

    t = sub.add_parser("trim", help="DESTRUCTIVE guarded TRIM/discard (you must own the drive)")
    t.add_argument("--device", required=True)
    t.add_argument("--confirm", default="")
    t.add_argument("--confirm-device", default="")
    t.set_defaults(func=cmd_trim)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
