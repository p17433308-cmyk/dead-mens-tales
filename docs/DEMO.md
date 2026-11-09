# Verified Demo — Real Delete + TRIM Persistence

A reproducible, hardware-free demonstration of the core thesis, run on a Linux
loopback device with real `fstrim`. It proves the *block-layer* mechanism:
deleted and TRIMmed data can persist in the raw medium. (It does NOT emulate a
specific SSD controller's DZAT/DRAT behaviour — that still needs real hardware;
see "Scope".)

## Run it

```bash
sudo scripts/loop_canary.sh /tmp/bs_canary
```

Creates a 64 MiB image on a loop device mounted `-o discard`, writes a canary
file, locates it by searching the raw device for its magic string, captures
read maps before and after a real `fstrim`, and emits an examiner report.

## Verified result (RTX box, WSL Ubuntu, kernel 6.6, 2026-11-09)

```
found canary magic at byte 8589312 -> physical LBA 16776
[*] CAPTURE BEFORE delete  -> VERDICT: ALIVE
    bytes at canary LBA (before): BLACKSPOT-CANARY-XMARKSTHESPOT
[*] deleting canary + issuing real fstrim
    /tmp/bs_canary/mnt: 55.8 MiB (58519552 bytes) trimmed
[*] CAPTURE AFTER delete+TRIM -> VERDICT: ALIVE
    bytes at canary LBA (after):  BLACKSPOT-CANARY-XMARKSTHESPOT
```

**The point:** the OS reported deleting the file and trimming 55.8 MiB, yet the
"treasure" is still readable in the raw blocks afterward. Absence of a file at
the filesystem layer is not absence of the data at the medium layer. This is the
whole talk, demonstrated live, with nothing staged.

## Why it's honest

- Real `fstrim`, real kernel discard path, real raw-device reads — no mocking.
- We locate the data by grepping the raw device, so there's no sleight of hand.
- The verdict comes from the same BLACKSPOT engine shipped in the tool.

## Scope / what this does and does not show

- **Does show:** deleted + TRIMmed data persisting in the raw medium, and the
  triage engine classifying it correctly from real captures.
- **Does NOT show:** a physical SSD controller's post-TRIM behaviour (DZAT vs
  DRAT vs non-deterministic). A loopback device has no FTL or garbage collector.
  Demonstrating controller masking requires a real throwaway SSD (pending).
- Use this as the guaranteed, portable fallback demo; use a real drive for the
  controller-fingerprinting headline when hardware is available.
