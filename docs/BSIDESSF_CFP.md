# BSidesSF 2027 — CFP Submission
## Dead Men Tell No Tales: Triaging SSDs That Lie About Deleted Data

**Conference:** BSidesSF 2027 · Pier 27, San Francisco · April 3–4, 2027
**Track:** DFIR / Forensics (with anti-forensics crossover)
**Theme tie-in:** 🏴‍☠️ Pirates — the *black spot*, scuttled ships, "dead men tell no tales"
**Tool release:** BLACKSPOT (open-source, Apache-2.0) — first open tool for host-side SSD triage
**Repo:** https://github.com/p17433308-cmyk/dead-mens-tales

---

## Submission A — Presentation (45 minutes)

### Title
**Dead Men Tell No Tales: Triaging SSDs That Lie About Your Deleted Data**

### Abstract (submission version, ~200 words)

Every forensics course teaches that a deleted file lingers until it's
overwritten. On SSDs, that's a lie — and worse, the drive itself may be lying to
*you*. TRIM, background garbage collection, and the Flash Translation Layer mean
a deleted block is sometimes physically gone and unreachable, and sometimes fully
intact in NAND while the controller cheerfully returns zeros to every read you
issue (DZAT). Investigators find out which — after a $3,000 destructive chip-off.

This talk flips the order. We show how to **fingerprint a controller's post-TRIM
behavior host-side**, in minutes, to decide whether the treasure is still aboard
or already scuttled — *before* committing to chip-off. We cover DRAT vs DZAT vs
non-deterministic TRIM, how to catch a drive masking live NAND data, the pre-GC
recovery window and how to preserve it, and exactly where self-encrypting drives
end the hunt for good.

We release **BLACKSPOT**, the first open-source host-side SSD triage tool, with a
printable "is recovery plausible on THIS drive?" decision tree. Live demo on two
controller families recovering a planted canary from a "wiped" drive — and one
case where the drive insists it's empty while the data is right there.

### Takeaways
- A repeatable method to classify SSD recoverability *without* a lab.
- The BLACKSPOT tool + a one-page field decision tree they can use Monday.
- A clear, physics-grounded understanding of when to chip-off and when to quit.

### Why BSidesSF / why now
SSD forensics is a perennial DFIR blind spot that the main-stage circuit
under-serves. The one genuinely novel framing — *controller behavior as evidence*
(the drive lies) — has strong crossover appeal to the anti-forensics/offense
crowd. It's practitioner-first, demo-driven, and ships a tool.

### Novelty / prior-art delta (for reviewers)
Prior work (Wei et al. 2011; Scanlon et al.; arXiv 2307.10192; ElcomSoft 2025)
establishes that remnants persist and that chip-off can reach them. **None ships
an open host-side triage tool that decides recoverability and detects DZAT
masking before chip-off.** That decision layer is our contribution. See
[NOVELTY.md](NOVELTY.md).

### Outline → see [TALK_OUTLINE.md](TALK_OUTLINE.md)

### Speaker prerequisites for audience
Comfort with basic storage/forensics terms. No flash-engineering background needed.

---

## Submission B — Workshop (120 minutes)

### Title
**Scuttled or Seaworthy? Hands-on SSD Triage with BLACKSPOT**

### Abstract (~150 words)

A hands-on, laptop-only workshop. We hand you capture files from real controller
families — some where deleted data is readable, some where the drive returns
zeros while NAND still holds the evidence, one crypto-erased decoy — and you learn
to tell them apart. You'll run BLACKSPOT, read its fingerprint output, walk the
recoverability decision tree by hand, and defend your verdict as if cross-examined.

By the end you can look at a drive in the field and answer the only question that
matters before a chip-off: *is the treasure still aboard?*

### Format & logistics
- **Capacity:** 25–40. **Bring:** a laptop with Python 3.9+. No hardware, no root.
- Everything runs on provided reproducible capture files (safe, offline).
- Materials: BLACKSPOT repo, capture packs, printed decision trees, verdict worksheet.

### Agenda → see [WORKSHOP.md](WORKSHOP.md)

---

## Logistics / boilerplate
- **Vendor pitch?** No. Non-profit/open-source research + tool release.
- **AV needs:** projector/HDMI; terminal-heavy; live demo (recorded fallback ready).
- **Co-presenters / panel:** TBD.
- **Prior venues for this material:** none — BSidesSF premiere.
