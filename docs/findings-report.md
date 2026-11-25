# Findings report — Consolidated PostFiat Governance-Audit Framework

Pinned postfiatd commit: `0085a1ff885d6a446369cf73a4430f75af22be55`.
Severity: **1 HIGH, 6 MEDIUM, 3 LOW, 1 INFO** across 11 scenarios
(G0–G10). Full matrix: `outputs/matrix.json` / `.csv` — every row
carries `output_path`, the committed raw output file it cites.
Labels: **SIMULATED** = produced by the harness;
**OBSERVED** = read directly from a primary source (cited).

## HIGH

### F1 — An enabled amendment cannot be rolled back (G4)

- **Measured (SIMULATED):** the rollback attempt on enabled
  `fixCritical` failed (1 attempt, 1 failure). Per-node ledger replay
  of 100 ledgers re-executed history without changing the enabled
  amendment (`outputs/G4-emergency-upgrade-no-rollback.json`).
- **OBSERVED:** xrpl.org Amendments (re-fetched 2026-11-25):
  "Disabling a passed amendment requires a new amendment to do so."
  No rollback path exists in the assessed code, and no primary source
  describing a rolled-back activated amendment was found (searched,
  not found — see `docs/research-notes.md` §5.4).
- **Implication:** a faulty activation can only be fixed forward — by
  a new amendment (another 14-day hold, unless the fix itself bypasses
  the vote as in the xrpld 3.4.1 precedent) or by a binary upgrade
  with amendment-blocked enforcement. There is no undo. The safety
  must therefore be pre-activation: the 14-day hold, veto, and
  DefaultNo gating are the only brakes.
- **Controls:** C18 (UNMEASURED — absent), C16, C17.

### F2 — The 14-day amendment wait is too slow for an active exploit (G4)

- **Measured (SIMULATED):** `fixCritical` (DefaultYes, 35/35 support)
  enabled on day 14.0207 — the full hold, with no fast path.
  (`outputs/G4-emergency-upgrade-no-rollback.json`).
- **OBSERVED:** the xrpld 3.4.1 precedent (Oct 2026): a Critical
  payment-engine overflow fix was shipped "as a direct change rather
  than an amendment" because the 80%-for-two-weeks wait was judged too
  slow; servers not on 3.4.1+ became amendment-blocked
  (`docs/research-notes.md` §5.2).
- **Implication:** PostFiat's emergency path is a binary upgrade plus
  amendment-blocked enforcement, not the amendment process. Operators
  must be ready to roll a binary in hours, and the network must accept
  that slow upgraders become blocked. No runbook for that path exists
  in the assessed code or docs (see F8).

## MEDIUM

### F3 — A minority can pass an amendment during a partial outage (G1)

- **Measured (SIMULATED):** 12 validators offline for 5 days:
  108,000 ledgers missed (23 online < quorum 24). During the outage
  the threshold denominator shrank to the 23 validations received
  (threshold 15), so the 23-vote minority (65.7% of the UNL) gained
  majority on day 5.0119; on recovery the bar returned to 24 and the
  majority was lost on day 10.0119 after holding 5.0 days — 1 restart,
  never enabled (`outputs/G1-quorum-failure-minority-majority.json`).
- **OBSERVED:** `AmendmentSet` computes the threshold from
  `trustedValidations_` — the count of trusted validations received
  (`AmendmentTable.cpp:323-351`), and `TrustedVotes` expires votes
  from validators unheard from (`AmendmentTable.cpp:93-108`). The
  threshold is relative to validations received, not to UNL size.
- **Implication:** an amendment that cannot pass at full attendance
  can gain majority during a partial outage. If the outage lasts the
  full 14-day hold, the minority amendment enables. This is the
  single most consequential interaction in the pack: quorum failure
  does not freeze governance, it lowers the bar. Mitigation is
  operational (restore validators fast; watch majority gains during
  outages) — there is no code gate that freezes amendment voting
  while the network is below quorum.
- **Controls:** C00, C06.

### F4 — A veto deadlock needs only 12 vetoes to stall an amendment indefinitely (G2)

- **Measured (SIMULATED):** 12 vetoes cut support 30 → 18 on day 3
  (majority lost after holding 3.0 days); one un-veto raised it to 19,
  still below the 24-vote bar; the amendment never enabled over 21
  days. `unknownFeature` (no code) never entered voting
  (`outputs/G2-veto-deadlock.json`).
- **OBSERVED:** veto persists in the wallet DB until explicitly
  un-vetoed (`AmendmentTable.cpp:736-762`); unknown amendments are
  effectively vetoed already (`AmendmentTable.cpp:648`).
- **Implication:** 12 of 35 validators (34.3%) can block any amendment
  forever, and there is no expiry or override on a veto. That is the
  designed veto power — but it means a determined minority can hold a
  critical fix hostage, and the only remedy is persuasion (or the
  binary-upgrade bypass of F2). Operators should treat a veto count
  near 12 as a governance incident, not a routine disagreement.
- **Controls:** C03, C04.

### F5 — A 2-hour support dip costs 12 banked days (G7)

- **Measured (SIMULATED):** majority held 12.0 days, then support
  dipped to 22/35 for one flag-ledger interval; the majority was lost
  and the 14-day clock restarted; the amendment enabled day 26.1207
  — 12.1 days later than the day-14.0207 baseline
  (`outputs/G7-majority-loss-clock-restart.json`).
- **OBSERVED:** xrpl.org Amendments (re-fetched 2026-11-25): "If
  support drops below 80%, the amendment is temporarily rejected, and
  the two week period restarts." The `fixCleanup3_4_0` incident (Oct
  2026, secondary source) shows the same rule costing 12 days on the
  live network (`docs/research-notes.md` §5.3).
- **Implication:** the clock has no grace period and no partial
  credit. Any transient dip — a validator restart wave, a brief
  outage — resets the hold. Operators planning an activation should
  keep support well above the bar (not at 24-25 of 35) until
  enablement, and should expect the date to slip on any dip.
- **Controls:** C01.

### F6 — No treasury control exists (G5)

- **Measured (SIMULATED):** the fee vote split 12/12/11 across
  10/12/15 drops with target 12; the 15-drop votes fell outside
  [current, target] and were discarded, the 10/12 tie kept the fee at
  10 drops; 0 fee changes
  (`outputs/G5-treasury-fee-gap.json`).
- **OBSERVED:** "treasury": 0 hits in `src/` (case-insensitive,
  whole checkout) and 0 hits in the 677-line whitepaper (fetched
  2026-11-25). Fees burn; there is no validator subsidy and no
  treasury mechanism to govern.
- **Implication:** fee votes are the only economic control. There is
  no on-chain treasury, no spending policy, and no governance path
  for one. If PostFiat later adds a treasury (the whitepaper's NAVCoin
  issuance and fee flows suggest economic activity will need one),
  that is a new governance surface with no precedent in the assessed
  code. Do not assume treasury controls exist because fee votes do.
- **Controls:** C15 (UNMEASURED — absent), C13.

### F7 — Amendment-blocked validators shrink the safety margin (G9)

- **Measured (SIMULATED):** 5 validators on old binaries became
  amendment-blocked when `fixExample` enabled (day 14.0207). The
  network kept validating (30 online ≥ quorum 24) and `fixSecond`
  still enabled (day 34.0207, threshold 20 at 30 validations — the
  denominator shrank again), but the safety margin shrank from 11 to
  6 validators (`outputs/G9-amendment-blocked-divergence.json`).
- **OBSERVED:** blocked servers cannot determine ledger validity,
  submit/process transactions, participate in consensus, or vote on
  future amendments (xrpl.org, re-fetched 2026-11-25). Unblock only
  by upgrading.
- **Implication:** slow upgraders do not just lag — they subtract from
  the network's fault tolerance while remaining on the UNL. With 5
  blocked, 6 further failures halt the chain where 11 could before.
  The UNL should be pruned of persistently blocked validators (via
  publisher lists), or the quorum math should count only
  unblocked validators. Neither happens automatically.
- **Controls:** C17, C06.

### F8 — An operator can shrink the 14-day hold to 15 minutes (G10)

- **Measured (SIMULATED):** with `AMENDMENT_MAJORITY_TIME` set to 15
  minutes, `fixExample` enabled day 0.0237 (34 minutes) instead of
  day 14.0207 — the hold collapsed 14 days → 15 minutes (1344x
  shorter); end-to-end enablement was 591x faster
  (`outputs/G10-majority-time-override.json`).
- **OBSERVED:** the hold defaults to 2 weeks (`Config.h:248`) but is
  operator-configurable via `[amendment_majority_time]`, with a
  15-minute floor (`Config.cpp:872-895`). The setting is per-server:
  each validator's own hold governs its own vote, and there is no
  network-wide check that the hold was shortened.
- **Implication:** the 14-day safety window is a local default, not a
  network invariant. A single operator shortening the hold does not
  by itself enable an amendment (the majority is still counted across
  validators), but a coordinated shortening — or a widely copied
  config — collapses the review window the whole process depends on.
  The hold should be treated as a governance parameter (agreed
  network-wide, monitored), not a local tuning knob.
- **Controls:** C01.

## LOW

### F9 — Key compromise is recoverable — rotation works, revocation is permanent (G3)

- **Measured (SIMULATED):** V07 signing-key compromise recovered by
  1 manifest rotation (sequence 1 → 2) with no validation
  interruption. V11 master-key compromise required 1 revocation
  manifest (sequence 0xFFFFFFFF); the validator left the UNL
  (35 → 34) and the quorum recomputed 24 → 23
  (`outputs/G3-compromised-validator-key.json`).
- **OBSERVED:** manifest structure (master + ephemeral key +
  sequence; revoke at 0xFFFFFFFF) — `Manifest.h:44-76, 133-141`.
- **Implication:** the key-compromise response works as designed, but
  it is entirely manual: no automation rotates a compromised signing
  key, and revocation is irreversible — a revoked master key can never
  come back. Operators need a tested runbook for both paths, and a
  pre-staged replacement validator for the revocation case.
- **Controls:** C09, C10.

### F10 — Publisher redundancy holds until 2 of 3 publishers are down (G6)

- **Measured (SIMULATED):** one publisher down: quorum held at 24.
  Two of three down: quorum disabled for 84 flag ledgers and 21,600
  ledgers missed until a publisher returned. 3 unreliable validators
  lowered the effective UNL to 32 and the quorum to 22. One exclusion
  (24/35 agreement) applied at one change per 10 ledgers
  (`outputs/G6-publisher-churn-negative-unl.json`).
- **OBSERVED:** listThreshold 2 of 3 (`ValidatorList.cpp:197-215`);
  quorum disabled at the error threshold
  (`ValidatorList.cpp:1861-1893`); negative-UNL thresholds
  (`NegativeUNLVote.h:50-80`); exclusion rate
  (`docs/Exclusions.md:41`).
- **Implication:** the publisher layer is the single point of
  liveness failure: 2 of 3 publishers down halts the chain. Publisher
  diversity (independent operators, independent hosting) matters as
  much as validator diversity. The negative UNL softens the blow for
  unreliable validators but does not help against publisher loss.
- **Controls:** C07, C08, C11, C12.

### F11 — Fee votes stall on splits; silent validators count as no-votes (G5, G8)

- **Measured (SIMULATED):** G5: 12/12/11 split, 0 changes. G8:
  18/17 split on owner reserve kept 2 XRP; 18 submitted a base-fee
  field while 17 counted as noVote; 0 changes
  (`outputs/G8-fee-vote-split-reserves.json`).
- **OBSERVED:** `VotableValue::getVotes` takes the most-voted value
  between current and target, inclusive (`FeeVoteImpl.cpp:70-85`);
  only trusted validations vote (`FeeVoteImpl.cpp:196-280`).
- **Implication:** the fee vote moves only on a modal majority. A
  split field cannot move even when a majority of voters want some
  change, and validators that stay silent vote for the status quo by
  omission. Fee changes need an explicit, coordinated modal position
  — a bare "we should raise fees" consensus is not enough.
- **Controls:** C13 (PARTIAL).

## INFO

### F12 — Baseline: the full stack works under normal conditions (G0)

- **Measured (SIMULATED):** 30/35 support, threshold 23, majority
  day 0.0119, enabled day 14.0207; quorum 24; 324,000/324,000 ledgers
  validated, 0 missed; base fee unchanged at 10 drops
  (`outputs/G0-baseline-full-governance.json`).
- The governance stack — amendment vote, 14-day hold, validation
  quorum, fee vote — functions as designed when all validators are
  online, all publishers are up, and support is comfortably above the
  bar. Every other finding in this report is about what happens when
  one of those conditions breaks.
