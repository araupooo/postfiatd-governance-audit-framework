# Environment — Consolidated PostFiat Governance-Audit Framework

## Build environment

- Python 3, standard library only (no third-party packages).
- No postfiatd build, no live node, no network access required to run
  the harness. `bash scripts/run_all.sh` runs the full reproduction
  offline.
- The pack was built and verified on a Linux VM; any POSIX system
  with Python 3 and `bash` reproduces it.

## What was NOT run

- **No postfiatd node was built or run.** The simulator
  (`scripts/simulator.py`) re-implements the cited decision logic
  from the pinned source; it is a model of the governance rules, not
  an execution of the code. This is the pack's central limitation:
  every measured number is SIMULATED.
- **No live PostFiat network was observed.** Whether the post-fix
  67% threshold has ACTIVATED on any live PostFiat network is
  UNVERIFIED — it requires a live ledger Amendments-object check,
  which was not performed. The pack assumes the post-fix rule (67%,
  strict `>`) because `fixAmendmentMajorityCalc` is registered as
  `Supported::yes` with `VoteBehavior::DefaultYes` in the pinned
  code; activation on a live network is a separate check.
- **No GitHub API cross-check of blob SHAs succeeded.** The GitHub
  API tree and commits endpoints returned HTTP 403 (rate-limited for
  the shared egress IP) at build time on 2026-11-25. Blob SHAs in
  `docs/source-inventory.md` are the local `git hash-object` values
  from the checkout at the pinned commit — the same SHA-1 git assigns
  to the blob — and every cited line was read from that checkout.
  The pack's own files are proven by the fresh-clone reproduction
  instead (see below).

## Fidelity notes

- One ledger close = 4 s virtual time (a modeling choice; the pinned
  code does not fix a close interval). Day counts are virtual days at
  4 s per ledger; ledger counts and event ordering are the invariant
  quantities.
- During a quorum outage the real network closes no ledgers, so no
  flag ledger occurs and the amendment clock freezes. The model still
  evaluates flag ledgers on virtual time during outages. Missed-ledger
  counts are the conservative measure; amendment timing inside an
  outage is an upper bound. G1's finding (minority majority) is
  stated with its mechanism and does not depend on the clock
  continuing during the outage — the majority is gained because the
  denominator shrinks, not because time passes.
- `TrustedVotes` expiry is modeled as "validations received = online
  trusted validators". Transient expiry windows are not modeled.
- Fee votes are evaluated with constant ballots at each flag ledger;
  the outcome repeats, so the model records the outcome once per
  advance. Fee-change counts are unaffected.
- The harness submits no transactions: fee burn (C14) is not
  exercised, and no ledger contents exist beyond sequence numbers
  and fee fields.

## Reproduction

```
bash scripts/run_all.sh
```

Runs the harness, builds the matrix and controls, writes the
manifest and SHA256SUMS, and verifies digests. Exit 0 on success.
The committed fresh-clone transcript
(`outputs/fresh-clone-reproduction.log`) records a clean-checkout
run: `run_all.sh` exit 0, outputs byte-identical (excluding the run
log), `verify_digests.sh` 68/68 OK exit 0, and the manifest SHA
matching the committed `manifest.json`.

## File layout

```
README.md
SHA256SUMS
manifest.json
.gitignore
scripts/        simulator, harness loader, matrix/control builders,
                manifest + digest tooling, run_all, transcript maker
docs/           source-inventory, control-inventory, methodology,
                findings-report, remediation-report, decision-memo,
                environment, research-notes
scenarios/      G0-G10 scenario definitions (JSON)
outputs/        scenario JSONs + CSVs, controls, matrix,
                fresh-clone-reproduction.log, run_all.log
```
