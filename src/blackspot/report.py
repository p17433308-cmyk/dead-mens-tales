"""Court-style examiner report generation from a TriageResult.

Produces a plain, defensible Markdown report an examiner can attach to a case
file. Every statement traces to an observed fact or a physical property of the
media, never to speculation.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .models import TriageResult

_PLAIN_FINDING = {
    "alive": "Deleted data is, or was at capture time, reachable from the host "
             "interface. Recovery by host-side imaging is viable.",
    "lying": "The host interface returns zeros for the examined ranges, but the "
             "controller's deterministic-zero-after-TRIM behaviour masks the "
             "underlying NAND. Absence of host-visible data does NOT establish "
             "that the data is physically erased. This is a chip-off candidate.",
    "fading": "The drive masks the examined ranges and has had an idle period in "
              "which background garbage collection is likely to be eroding "
              "invalidated pages. The recovery window is closing.",
    "scuttled": "No residual data was confirmed reachable from the host. This is "
                "stated as UNCONFIRMED; it is not affirmative proof of secure "
                "erasure.",
    "crypto_erased": "The device reports a confirmed cryptographic erase. The "
                     "media-encryption key is destroyed; recovery of plaintext "
                     "is not possible by any known means.",
}


def to_markdown(result: TriageResult, case_id: str = "UNASSIGNED",
                examiner: str = "", exhibit: str = "") -> str:
    d = result.drive
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    a = lines.append
    a("# SSD Recoverability Triage Report")
    a("")
    a(f"- **Case ID:** {case_id}")
    a(f"- **Exhibit:** {exhibit or 'n/a'}")
    a(f"- **Examiner:** {examiner or 'n/a'}")
    a(f"- **Generated:** {now}")
    a(f"- **Tool:** BLACKSPOT (host-side SSD triage)")
    a("")
    a("## 1. Device")
    if d:
        a(f"- Model: {d.model}")
        a(f"- Controller family: {d.controller_family}")
        a(f"- Self-encrypting (SED): {d.is_sed}")
        a(f"- Crypto-erase confirmed: {d.crypto_erase_confirmed}")
        a(f"- TRIM enabled: {d.trim_enabled}")
        a(f"- Power lost since TRIM: {d.powered_down_since_trim}")
        a(f"- Idle since delete (s): {d.idle_seconds_since_delete}")
    a("")
    a("## 2. Observed controller behaviour")
    a(f"- Post-TRIM read behaviour: **{result.trim_behavior.value}**")
    a(f"- Classification confidence: **{result.confidence:.0%}**")
    a("")
    a("## 3. Finding")
    a(f"**Verdict: {result.verdict.value.upper()}**")
    a("")
    a(_PLAIN_FINDING.get(result.verdict.value, ""))
    a("")
    a("## 4. Basis")
    for r in result.rationale:
        a(f"- {r}")
    a("")
    a("## 5. Recommended action")
    a(result.recovery_window_note)
    a("")
    a("## 6. Limitations")
    a("- This triage classifies host-side reachability and controller masking; "
      "it does not itself recover garbage-collected or over-provisioned pages, "
      "which are not addressable from the host interface by design.")
    a("- A confirmed SED cryptographic erase is irreversible.")
    a("- Findings reflect device state at capture time; controller background "
      "activity may change reachability thereafter.")
    return "\n".join(lines) + "\n"
