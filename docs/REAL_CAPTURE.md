# Verified Real Capture — genuine kernel TRIM behaviour

Proof that BLACKSPOT's triage runs on **real block-layer artifacts**, not just
synthetic captures. It uses Linux loop devices, so it is reproducible and risks
no physical disk — while the TRIM/discard it reacts to is the real kernel ioctl.

## Reproduce

```bash
sudo scripts/real_capture.sh
```

Two scenarios, each a real kernel outcome captured by BLACKSPOT's own read-only
harness and classified by the real triage engine:

## Verified result (Linux, WSL2 kernel 6.6, 2026-11-09)

**Scenario 1 — deleted but NOT trimmed → ALIVE**
```
raw bytes after delete: BLACKSPOT-TREASURE-XMARKSTHESPOT
VERDICT: ALIVE  (DRAT) — 4/4 LBAs returned stable non-zero data; entropy 3.88
```
The file was deleted; its bytes persist in the raw device. BLACKSPOT reads them
back — host-side recovery is genuinely possible here.

**Scenario 2 — real `blkdiscard` (TRIM ioctl) → LYING**
```
raw bytes after discard: ''   (deterministic zeros)
VERDICT: LYING  (DZAT) — host sees zeros; on a real SSD those zeros can mask
                          live NAND. Chip-off candidate, not a confirmed wipe.
```
A real discard was issued; reads now return deterministic zeros. That is exactly
the DZAT behaviour BLACKSPOT flags as the drive potentially *lying* about what it
still holds.

## What this proves, and its limit

- **Proves:** BLACKSPOT's capture harness + triage engine correctly classify real
  kernel read-after-delete and read-after-discard behaviour end-to-end.
- **Limit (honest):** a loop device has no SSD controller, FTL, or garbage
  collector, so this demonstrates the TRIM/discard *mechanism* and the DZAT/DRAT
  read behaviours — not a specific vendor controller's masking. Fingerprinting a
  real controller still requires a throwaway physical SSD; this is the guaranteed,
  portable fallback demo.
