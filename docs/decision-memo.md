# Decision memo — Consolidated PostFiat Governance-Audit Framework

Pinned postfiatd commit: `0085a1ff885d6a446369cf73a4430f75af22be55`.

## Decision requested

Adopt the governance-audit framework in this pack as the working
baseline for PostFiat validator governance, and accept the five
decisions below. No code change to the assessed commit is required to
adopt the framework; the [CODE] items are proposals for future work.

## Background

The governance stack — amendment voting with a 67% threshold and a
14-day hold, a 67% validation quorum, publisher-list UNL, manifest
key management, fee votes, and amendment-blocked enforcement — was
assessed across 11 scenarios (G0–G10) covering all five governance
domains. The baseline (G0) works as designed under normal conditions.
Every material finding concerns what happens when one condition
breaks: an outage, a veto bloc, a support dip, a slow upgrade, or an
operator config change.

## Decisions

### 1. The 14-day hold is the last brake — treat it as such

An enabled amendment cannot be rolled back (F1). The only fix-forward
paths are a new amendment (another 14-day hold) or a binary upgrade.
Decision: **no amendment reaches majority without a completed
pre-activation checklist** (review, drafted replacement amendment,
tested emergency-upgrade path, veto monitoring) — see R1.

### 2. The emergency path is a binary upgrade, not the amendment process

The 14-day hold is too slow for an active exploit (F2), and the
precedent (xrpld 3.4.1) is a direct change bypassing the vote.
Decision: **publish an emergency-upgrade runbook** with go/no-go
criteria, a decision-maker, and a post-upgrade audit of the
amendment-blocked set — see R2.

### 3. Quorum failure lowers the governance bar — monitor it

During a partial outage the amendment threshold shrinks to the
validations received, so a minority can gain majority (F3). Quorum
failure does not freeze governance; it lowers the bar. Decision:
**alert on any amendment majority held while validations are below
UNL size**, and do not let an outage last the full hold with an
amendment at majority — see R3. A code gate freezing majority
counting below quorum is proposed for future work.

### 4. The majority-time hold is a governance parameter, not a local knob

An operator can set the hold to 15 minutes (F8), and there is no
network-wide check. Decision: **agree the hold network-wide (14-day
default), audit `[amendment_majority_time]` across validators
quarterly, and treat any value below 14 days as a governance
incident** — see R8.

### 5. There is no treasury — do not govern as if there were one

No treasury mechanism exists in the code or the whitepaper (F6). Fee
votes are the only economic control, and they stall on splits (F11).
Decision: **any future treasury is a new governance surface to be
designed and audited from scratch**; until then, fee changes require
an explicit, coordinated modal position — see R6, R10.

## What is NOT decided here

- Whether to change the 67% threshold or the 14-day hold in code.
  The values are the assessed code's; changing them is a separate
  governance decision requiring its own amendment.
- Whether the whitepaper's Cobalt ratification (q=24/35) should be
  implemented. The assessed code has no Cobalt implementation (0 hits
  in `src/`); the gap is recorded in `docs/research-notes.md` §5.5.
- Whether to adopt the [CODE] proposals (quorum-gated majority
  counting, removing the majority-time override). These are recorded
  for future work.

## Evidence base

- 11 scenarios, 19 controls (15 MEASURED, 1 PARTIAL, 3 UNMEASURED),
  severity 1 HIGH / 6 MEDIUM / 3 LOW / 1 INFO.
- All parameters traced to primary sources in
  `docs/source-inventory.md`; all results SIMULATED by the harness in
  `scripts/`; OBSERVED vs SIMULATED labels throughout.
- Reproduction: `bash scripts/run_all.sh` (see README.md), verified
  by a committed fresh-clone transcript
  (`outputs/fresh-clone-reproduction.log`).

## Risks if not adopted

- An amendment enables during an outage on minority support, with no
  rollback available (F3 + F1).
- A veto bloc of 12 stalls a critical fix with no expiry (F4).
- A support dip silently resets a 14-day hold (F5).
- Slow upgraders erode the safety margin while remaining on the UNL
  (F7).
- An operator shortens the hold network-wide with no check (F8).
