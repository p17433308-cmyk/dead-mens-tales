# The BLACKSPOT Decision Tree
### "Is recovery plausible on THIS drive?" — the one-page field takeaway

```
START: deleted/wiped SSD in hand
│
├─ Is it a SED with a CONFIRMED crypto-erase?
│     └─ YES → ☠ CRYPTO-ERASED. Key is gone. Stop. Pursue escrow/backups.
│
├─ Did the drive lose power AFTER the delete/TRIM but BEFORE background GC ran?
│     └─ YES → 🟢 ALIVE (pre-GC window). Image NOW with a write-blocker;
│              do not boot the host. Read before GC can fire.
│
├─ Repeated reads of trimmed LBAs return NON-ZERO data? (DRAT / non-deterministic)
│     └─ YES → 🟢 ALIVE. Residual data is host-reachable now. Capture before GC.
│
├─ Repeated reads return DETERMINISTIC ZEROS? (DZAT — the drive may be lying)
│     ├─ Idle > ~1h since delete? → 🟠 FADING. GC likely eroding pages.
│     │                              Escalate to chip-off FAST; window closing.
│     └─ Idle short?             → 🟡 LYING. Host sees zeros but NAND may be
│                                    intact. Chip-off candidate, NOT a confirmed
│                                    wipe. Document the DZAT masking.
│
├─ TRIM never reached the device (disabled / USB bridge / unsupported)?
│     └─ YES → 🟢 ALIVE. Treat like HDD-style recovery; carving likely works.
│
└─ None of the above / insufficient signal
      └─ ◼ SCUTTLED (unconfirmed). Preserve evidence and escalate.
```

## How to feed the tree
1. **Observe drive facts:** model, controller family, SED?, TRIM on?, power history,
   idle time since delete.
2. **Capture a read map:** read the same trimmed LBA ranges ≥3× with the device
   quiesced; hash each read; note all-zero vs non-zero.
3. **Run `blackspot triage --capture <file.json>`** or walk the tree by hand.
4. **Record the verdict + rationale** verbatim — it is court-defensible because
   every branch maps to a physically true statement.

## Why every branch survives cross-examination
- `CRYPTO-ERASED`: crypto-erase destroys the media key; mathematically irreversible.
- `ALIVE (pre-GC)`: data physically present until GC erases the page.
- `ALIVE (DRAT)`: controller literally returns the residual bytes host-side.
- `LYING (DZAT)`: DZAT masks reads; absence of host-visible data ≠ absence in NAND.
- `FADING`: background GC progressively erases invalidated pages over idle time.
- `SCUTTLED`: stated as *unconfirmed*, never as proof of wiping.
```
```
