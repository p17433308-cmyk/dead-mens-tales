# Dead Men Tell No Tales 🏴‍☠️
### BLACKSPOT — host-side SSD forensic triage & "the drive is lying to you" fingerprinting

> *The pirate's black spot was a mark of judgment. BLACKSPOT hands a verdict to a
> drive: is the deleted evidence still **alive** in NAND, or already **scuttled**
> by garbage collection — before you burn thousands on a destructive chip-off?*

**Built for BSidesSF 2027 (Pier 27, Apr 3–4).** DFIR / anti-forensics track.

---

## The problem

Classic disk forensics assumes a deleted block stays readable until overwritten.
On SSDs that assumption is quietly **false**. TRIM, background garbage collection
(GC), wear-leveling and the Flash Translation Layer (FTL) mean:

- A logically-deleted LBA may already be physically erased by GC — unreachable
  from the host *by design*.
- Or the data may be **fully intact in NAND** while the controller returns zeros
  to every host read (DZAT) — the drive is *lying to you*.
- Which of these is true depends on the controller family, TRIM determinism,
  idle time, and whether the drive lost power before GC fired.

Investigators currently find out *after* a $2–5k chip-off. That's backwards.

## What BLACKSPOT does (and honestly does NOT)

It does **not** magically recover garbage-collected pages host-side — once a
controller erases a physical page, the host path cannot reach it. That's physics.

Instead BLACKSPOT is a **triage** tool:

1. **Fingerprints controller post-TRIM behavior** — DZAT / DRAT / non-deterministic
   — from repeated reads of the same trimmed LBAs. Detects when a drive returns
   zeros while NAND likely still holds the data.
2. **Classifies recoverability** via an explicit, auditable decision tree.
3. **Emits a court-friendly verdict + rationale** so you know whether to image
   now, escalate to chip-off, or stop.

Verdicts (the "black spots"): `ALIVE` · `LYING` · `FADING` · `SCUTTLED` · `CRYPTO-ERASED`.

## Quick start

```bash
python3 tests/test_triage.py            # run the test suite
PYTHONPATH=src python3 -m blackspot.cli triage --capture samples/example_dzat.json
PYTHONPATH=src python3 -m blackspot.cli triage --capture samples/example_drat.json --json
```

All analysis runs on captured **read maps** (JSON) — fully reproducible offline
and safe to run in a workshop without touching live hardware.

## Repo layout

```
src/blackspot/        core library (fingerprint + triage engine + CLI)
samples/              example capture files (DZAT / DRAT / crypto-erased)
tests/                smoke tests for the decision tree
docs/                 CFP submissions, talk outline, workshop, decision tree, novelty
```

## Scope honesty

Modern self-encrypting drives doing a **confirmed crypto-erase** defeat all of
this instantly — the key is gone, recovery is impossible, and BLACKSPOT says so
(`CRYPTO-ERASED`). Everything here targets the enormous installed base that is
*not* crypto-erasing: consumer drives, TRIM-only wipes, and misconfigured SEDs.

## License

Apache-2.0. Research/educational use for authorized forensic investigation.
