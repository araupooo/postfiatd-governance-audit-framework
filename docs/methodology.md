# Methodology — Consolidated PostFiat Governance-Audit Framework

## What was assessed

The governance controls of postfiatd at pinned commit
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10), across five
domains: (1) amendment quorum and veto, (2) validator-set governance
and key compromise, (3) treasury and fee controls, (4) upgrade
procedures, (5) rollback procedures. Every control parameter in the
simulator is taken verbatim from the pinned code and traced to its
file:line in `docs/source-inventory.md`.

## The simulator

`scripts/simulator.py` re-implements the decision logic of the cited
functions over a modeled validator set. It does NOT build or run
postfiatd. The model:

- **Time:** virtual days. One ledger close = 4 s (a modeling choice;
  the pinned code does not fix a close interval). 21,600 ledgers per
  day. A flag ledger falls every 256 ledgers (`Ledger.h:426`), i.e.
  every 1,024 s of virtual time.
- **Validator set:** 35 trusted validators by default (the whitepaper's
  stated committee size, §1.8), each with a manifest (master key,
  ephemeral signing key, sequence), online/offline state, and binary
  version. 3 publisher lists by default.
- **Amendment voting:** evaluated at every flag ledger, following
  `AmendmentTableImpl::doVoting` — `tfGotMajority` when validators
  have a majority but the ledger does not, `tfLostMajority` when the
  ledger has one but validators do not, enablement (action 0) when
  the majority has held for `majorityTime_` (default 14 days) and the
  local vote is up.
- **Threshold:** computed from the number of trusted validations
  received at the flag ledger, exactly as `AmendmentSet` does
  (`AmendmentTable.cpp:323-342, 360-378`): post-fix
  `max(1, floor(n * 67 / 100))` with strict `>`; pre-fix
  `max(1, floor(n * 204 / 256))` with `>=`; one-validator `>=`
  exception. This is the property G1 measures: the denominator is
  validations received, not UNL size.
- **Validation quorum:** `max(ceil(0.67 * effective_UNL),
  ceil(0.60 * UNL_size))`, disabled (returns the maximum value) when
  unavailable publishers reach the error threshold
  (`ValidatorList.cpp:1845-1935`).
- **Fee vote:** `VotableValue` — the most-voted value between current
  and target, inclusive; ties keep the current value; validators that
  submit no fee field count as noVote
  (`FeeVoteImpl.cpp:70-85, 196-280`).
- **Manifests:** rotation issues a new ephemeral key at sequence+1;
  revocation issues sequence `0xFFFFFFFF`, after which no further
  manifest for that master key is accepted (`Manifest.h:44-76,
  133-141`).
- **Exclusion:** 67% agreement queues a change; changes apply at one
  per 10 ledgers (`docs/Exclusions.md:5, 41, 184, 191`).
- **Amendment-blocked:** a validator on an old binary becomes blocked
  when any amendment enables; blocked validators neither validate nor
  vote (xrpl.org "Amendment Blocked Servers").
- **Rollback:** the model implements the documented reality — there is
  no in-protocol rollback. A rollback attempt always fails; per-node
  ledger replay re-executes ledgers without changing enabled
  amendments.

## OBSERVED vs SIMULATED

- **OBSERVED** means read directly from a primary source: a file:line
  in the pinned checkout, a fetched page (xrpl.org, whitepaper), or a
  counted search result (e.g. 0 "treasury" hits). OBSERVED claims
  carry their citation.
- **SIMULATED** means produced by the harness: every number in
  `outputs/G*.json`, `outputs/matrix.json`, and
  `outputs/controls.json` is SIMULATED. The parameters, gates, and
  thresholds are the pinned code's; the validator behaviour, vote
  splits, outages, and key events are deterministic stand-ins. No
  live postfiatd node was run (see `docs/environment.md`).

## Scenario list

| ID | Domain | Severity | What it measures |
|---|---|---|---|
| G0 | all (baseline) | INFO | Normal operation: 30/35 support, 14-day hold, quorum 24 |
| G1 | 1 + 2 | MEDIUM | Quorum failure + minority amendment majority during outage |
| G2 | 1 | MEDIUM | Veto deadlock (12 vetoes) + code-less amendment veto |
| G3 | 2 | LOW | Signing-key rotation + master-key revocation |
| G4 | 4 + 5 | HIGH | Emergency upgrade timing + no rollback path |
| G5 | 3 | MEDIUM | Treasury absence + split fee vote |
| G6 | 2 | LOW | Publisher churn, negative UNL, exclusion rate |
| G7 | 1 | MEDIUM | Majority-loss clock restart |
| G8 | 3 | LOW | Fee-vote split on reserves + silent validators |
| G9 | 2 + 4 | MEDIUM | Amendment-blocked divergence, safety margin |
| G10 | 1 | MEDIUM | Majority-time override to the 15-minute minimum |

## Determinism

No wall clock, no random module. All counts are integers; all times
are exact multiples of the flag-ledger interval (1,024 s). A second
run of `bash scripts/run_all.sh` reproduces `outputs/` byte-for-byte
(excluding the run log `outputs/run_all.log`). Verified during the
build: two consecutive full runs diffed identical.

## Model limitations (read before reusing the numbers)

1. **Flag ledgers during a quorum outage.** In the real network, no
   ledgers close during a quorum outage, so no flag ledger occurs and
   the amendment majority clock freezes. The model still evaluates
   flag ledgers on virtual time during outages (G1, G6). The
   missed-ledger counts are the conservative measure; amendment
   timing inside an outage is an upper bound on what the real network
   would do. No scenario's headline depends on a majority being
   gained *only* inside an outage window except G1, where the
   minority-majority effect is the finding itself and is stated with
   its mechanism (denominator = validations received).
2. **TrustedVotes expiry.** The real `TrustedVotes` keeps per-validator
   votes with a timeout; a validator unheard from long enough has its
   votes expire. The model treats "validations received" as "online
   trusted validators", which matches the steady state. Transient
   expiry windows (a validator that just went offline still having
   unexpired votes) are not modeled.
3. **One ledger close = 4 s.** The pinned code does not fix a close
   interval. Day counts in the outputs are virtual days at 4 s per
   ledger; a faster or slower network shifts wall-clock days, not the
   ledger counts or the ordering of events.
4. **Fee votes are cast once per advance segment.** The code evaluates
   the fee vote at every flag ledger; with constant ballots the
   outcome repeats, so the model evaluates the same ballots at each
   flag ledger and records the outcome once per advance. The fee-change
   counts are unaffected.
5. **No transaction flow.** The harness submits no transactions, so
   fee burn (C14) is not exercised, and no ledger contents exist
   beyond sequence numbers and fee fields.
6. **Whitepaper claims** (q=24/35, Cobalt, ML-DSA-65) are cited from
   the paper as read 2026-11-15; the paper was re-fetched 2026-11-25
   only for the "treasury"/"amend" absence checks. If the paper
   changes, re-verify those citations.

## Model bugs found and fixed during the build

1. `fee_votes` attribute/method name collision (TypeError on the first
   run) — fixed by renaming the ballot store to `fee_ballots`.
2. JSON object keys arrive as strings; fee-vote distributions
   (`{"10": 35}`) were compared against int bounds — fixed by
   coercing ballot keys to int in `fee_votes()`.
3. Amendment-blocked check first required the amendment itself to
   lack code; corrected to the documented rule — any enabled
   amendment blocks a node on an old binary (xrpl.org "Amendment
   Blocked Servers").
4. Per-flag-ledger "fee stays" log lines would have produced ~1,200
   identical lines per advance; removed — fee outcomes are recorded
   in the rows, and only fee *changes* log.
5. `Amendment.up_voters` was never initialised (AttributeError when
   no explicit support set exists) — fixed: `None` means "no explicit
   set", so DefaultYes votes up by default and DefaultNo votes down
   by default, matching `VoteBehavior`.
