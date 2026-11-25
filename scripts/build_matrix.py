#!/usr/bin/env python3
"""build_matrix.py — build the severity-ranked scenario matrix from the
unedited scenario outputs.

Usage: python3 scripts/build_matrix.py

Reads outputs/G*.json (written by scripts/load_harness.py) and writes:
  outputs/matrix.json — one entry per scenario with measured counts
  outputs/matrix.csv  — the same, one row per scenario

The matrix is derived, never hand-edited. Severity is assigned in the
scenario definition; this script ranks by severity (CRITICAL > HIGH >
MEDIUM > LOW > INFO) and attaches the measured numbers. Each row
carries output_path: the committed raw per-scenario output file it
cites, so a reviewer can spot-check traceability without the
claim-to-evidence index.
"""

import csv
import json
import os

RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

FIELDS = ["scenario_id", "title", "severity", "severity_reason",
          "output_path", "flag_ledgers", "ledgers_validated",
          "ledgers_missed", "amendments_enabled",
          "majority_restarts", "fee_changes",
          "exclusions_applied", "manifests_rotated",
          "manifests_revoked", "validators_blocked",
          "rollback_attempts", "rollback_failures",
          "replay_ledgers", "quorum_disabled_flag_ledgers",
          "unl_size", "online_trusted", "validation_quorum",
          "enabled_amendments"]


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(base, "outputs")
    entries = []
    for name in sorted(os.listdir(outdir)):
        if not name.endswith(".json") or not name.startswith("G"):
            continue
        with open(os.path.join(outdir, name), "r",
                  encoding="utf-8") as f:
            r = json.load(f)
        c = r["final"]["counters"]
        fin = r["final"]
        entries.append({
            "scenario_id": r["scenario_id"],
            "title": r["title"],
            "severity": r["severity"],
            "severity_reason": r["severity_reason"],
            "output_path": "outputs/%s.json" % r["scenario_id"],
            "flag_ledgers": c["flag_ledgers"],
            "ledgers_validated": c["ledgers_validated"],
            "ledgers_missed": c["ledgers_missed"],
            "amendments_enabled": c["amendments_enabled"],
            "majority_restarts": c["majority_restarts"],
            "fee_changes": c["fee_changes"],
            "exclusions_applied": c["exclusions_applied"],
            "manifests_rotated": c["manifests_rotated"],
            "manifests_revoked": c["manifests_revoked"],
            "validators_blocked": len(fin["blocked_validators"]),
            "rollback_attempts": c["rollback_attempts"],
            "rollback_failures": c["rollback_failures"],
            "replay_ledgers": c["replay_ledgers"],
            "quorum_disabled_flag_ledgers":
                c["quorum_disabled_flag_ledgers"],
            "unl_size": fin["unl_size"],
            "online_trusted": fin["online_trusted"],
            "validation_quorum": fin["validation_quorum"],
            "enabled_amendments": ",".join(
                sorted(n for n, a in fin["amendments"].items()
                       if a["enabled"])),
        })
    entries.sort(key=lambda e: (RANK[e["severity"]], e["scenario_id"]))
    with open(os.path.join(outdir, "matrix.json"), "w",
              encoding="utf-8") as f:
        json.dump(entries, f, indent=2, sort_keys=True)
        f.write("\n")
    with open(os.path.join(outdir, "matrix.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(entries)
    print("matrix: %d scenarios" % len(entries))


if __name__ == "__main__":
    main()
