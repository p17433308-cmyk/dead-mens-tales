"""BLACKSPOT — host-side SSD forensic triage & controller-behavior fingerprinting.

The pirate's "black spot" was a mark of judgment handed to a condemned man.
BLACKSPOT hands a verdict to a drive: is the deleted evidence still ALIVE in
NAND, or already SCUTTLED by garbage collection — *before* an investigator
spends thousands on a destructive chip-off.

This tool makes NO claim it can magically recover garbage-collected pages.
Once a controller erases a physical page, the host path cannot reach it — that
is physics, not a bug. What BLACKSPOT does instead:

  1. Fingerprint the controller's post-TRIM read behaviour (DRAT / DZAT /
     non-deterministic) — i.e. detect when the drive is *lying* (returning
     zeros while NAND still holds the data).
  2. Estimate the pre-GC recovery window and classify recoverability.
  3. Emit a defensible, court-friendly triage verdict + evidence log.

All analysis runs on captured "read maps" so it is fully reproducible offline
and safe to demo in a workshop without touching live hardware.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
