# Talk Outline — "Dead Men Tell No Tales" (45 min)

| # | Segment | Time | Beat |
|---|---------|------|------|
| 1 | Cold open: the drive that lied | 0–4 | Live: delete a file, `blackspot` says LYING, then show the bytes still in NAND. Hook. |
| 2 | Why HDD forensics breaks on flash | 4–10 | TRIM → GC → FTL → wear-leveling. The deleted-block assumption dies. |
| 3 | **Scope honesty up front** | 10–13 | SED crypto-erase = game over. Say it now so it can't eat your Q&A. Everything else is the real target. |
| 4 | Controller behavior as evidence | 13–22 | DZAT vs DRAT vs non-deterministic TRIM. The drive *masking* live data is itself a finding. ElcomSoft/Scanlon grounding. |
| 5 | The pre-GC recovery window | 22–28 | Power-cut timing, TRIM-disable-on-mount, read-before-GC. Where host-side recovery is *real*. |
| 6 | BLACKSPOT: fingerprint → verdict | 28–36 | Architecture, the decision tree, how each branch is physically defensible. |
| 7 | Live demo: 2 controller families | 36–41 | Canary recovery on a "wiped" drive; one DZAT masking case. Recorded fallback. |
| 8 | Decision tree takeaway + tool release | 41–44 | One-page field tree; repo URL; what's next (more controller families, crowd-sourced fingerprints). |
| 9 | Q&A | 44–45 | Pre-loaded: "what about SEDs?" already answered in seg 3. |

## The three things the audience must leave with
1. On SSDs, *absence of evidence is not evidence of absence* — the drive may be masking it.
2. A repeatable host-side triage method + tool, usable without a lab.
3. When to chip-off and when to quit — decided by physics, not hope.

## Demo risk management
- All live demos have a recorded fallback clip.
- Canary files + capture packs pre-staged; no dependence on venue network or hardware shipping.
