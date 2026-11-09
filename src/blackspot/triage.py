"""The decision-tree engine that produces the black spot (verdict).

Encodes the "is recovery plausible on THIS drive?" logic as explicit, auditable
rules — the attendee takeaway. Every branch maps to a physically defensible
statement, so the verdict survives expert cross-examination.
"""
from __future__ import annotations

from .models import DriveFacts, TriageResult, TrimBehavior, Verdict


def triage(drive: DriveFacts, behavior: TrimBehavior,
           behavior_confidence: float, behavior_rationale: list[str]) -> TriageResult:
    rationale = list(behavior_rationale)

    # 1. Crypto-erase short-circuits everything (kills the Q&A landmine).
    if drive.is_sed and drive.crypto_erase_confirmed:
        rationale.append(
            "SED reports a confirmed crypto-erase: the media-encryption key is "
            "destroyed. No host-side or chip-off recovery is possible."
        )
        return TriageResult(Verdict.CRYPTO_ERASED, behavior, 0.98,
                            "Abandon recovery. Pursue key escrow / backups only.",
                            rationale, drive)

    # 2. Power-cut before background GC ran => best case.
    if drive.powered_down_since_trim:
        rationale.append(
            "Drive lost power after TRIM but (apparently) before background GC "
            "erased the invalidated pages — classic pre-GC recovery window."
        )
        return TriageResult(Verdict.ALIVE, behavior, min(0.9, 0.6 + behavior_confidence / 3),
                            "Image immediately; do NOT power the drive in its host. "
                            "Use a write-blocker and read before GC can fire.",
                            rationale, drive)

    # 3. DRAT / non-deterministic => residual data is host-reachable right now.
    if behavior in (TrimBehavior.DRAT, TrimBehavior.NON_DETERMINISTIC):
        rationale.append(
            "Controller returns residual (non-zero) data on trimmed LBAs, so "
            "deleted content is at least partly readable without chip-off."
        )
        return TriageResult(Verdict.ALIVE, behavior, behavior_confidence,
                            "Host-side imaging viable now. Capture before further GC.",
                            rationale, drive)

    # 4. DZAT but firmware claims zero => the drive is LYING.
    if behavior == TrimBehavior.DZAT:
        if not drive.firmware_claims_zero:
            drive.firmware_claims_zero = True
        rationale.append(
            "Drive returns deterministic zeros, but DZAT means the NAND page may "
            "still hold the data — host reads are masked by the controller. This "
            "is a chip-off candidate, NOT a confirmed wipe."
        )
        # If GC has had a long idle window, physical erase grows likely.
        if drive.idle_seconds_since_delete and drive.idle_seconds_since_delete > 3600:
            return TriageResult(Verdict.FADING, behavior, 0.65,
                                ">1h idle since delete: background GC likely eroding "
                                "pages. Chip-off window is closing — escalate fast.",
                                rationale, drive)
        return TriageResult(Verdict.LYING, behavior, behavior_confidence,
                            "Host sees zeros but NAND may be intact. Escalate to "
                            "chip-off / vendor lab; document the DZAT masking.",
                            rationale, drive)

    # 5. No TRIM reached the device => conventional recovery likely.
    if behavior == TrimBehavior.NO_TRIM or not drive.trim_enabled:
        rationale.append("TRIM did not reach the device; treat closer to HDD-style recovery.")
        return TriageResult(Verdict.ALIVE, behavior, 0.8,
                            "Conventional carving/recovery likely effective.",
                            rationale, drive)

    rationale.append("Insufficient signal; default to cautious escalation.")
    return TriageResult(Verdict.SCUTTLED, behavior, 0.4,
                        "Unable to confirm residual data; preserve and escalate.",
                        rationale, drive)
