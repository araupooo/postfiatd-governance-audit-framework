#!/usr/bin/env python3
"""load_harness.py — run one governance scenario and write unedited outputs.

Usage: python3 scripts/load_harness.py scenarios/G0-*.json

Reads a scenario definition, drives scripts/simulator.py through its
steps, and writes three outputs named after the scenario id (for
example, scenario G0-baseline writes):
  outputs/G0-baseline.json  — full result (config, steps, final
                       state, counters, events, per-step rows)
  outputs/G0-baseline.csv   — one row per measured step outcome
  outputs/G0-baseline.log   — the simulator's own log lines,
                       unedited

Every number in the outputs comes from this script's run. Nothing is
hand-edited afterwards; digests are computed over the files as written.
"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from simulator import GovernanceNetwork, PINNED_COMMIT  # noqa: E402

CSV_FIELDS = ["scenario", "op", "kind", "outcome", "detail",
              "value", "unit"]


def run_scenario(path):
    with open(path, "r", encoding="utf-8") as f:
        scen = json.load(f)
    log = []
    net = GovernanceNetwork(scen["config"], log)
    rows = []
    step_results = []

    def row(op, kind, outcome, detail, value=None, unit=""):
        rows.append({"scenario": scen["id"], "op": op, "kind": kind,
                     "outcome": outcome, "detail": detail,
                     "value": value if value is not None else "",
                     "unit": unit})

    for i, step in enumerate(scen["steps"]):
        op = step["op"]
        res = {"step": i, "op": op}
        if op == "set_support":
            net.set_support(step["amendment"], step["up_voters"])
            res.update({"amendment": step["amendment"],
                        "up_voters": len(step["up_voters"])})
            row(op, step["amendment"], "set",
                "%d validators voting up"
                % len(step["up_voters"]), len(step["up_voters"]),
                "validators")
        elif op == "veto":
            net.veto(step["amendment"], step["validators"])
            res.update({"amendment": step["amendment"],
                        "validators": step["validators"]})
            row(op, step["amendment"], "vetoed",
                "vetoed by %s" % ",".join(step["validators"]),
                len(step["validators"]), "validators")
        elif op == "unveto":
            net.unveto(step["amendment"], step["validators"])
            res.update({"amendment": step["amendment"],
                        "validators": step["validators"]})
            row(op, step["amendment"], "unvetoed",
                "un-vetoed by %s" % ",".join(step["validators"]),
                len(step["validators"]), "validators")
        elif op == "set_online":
            net.set_online(step["validators"], step["online"])
            res.update({"validators": step["validators"],
                        "online": step["online"]})
            row(op, "validators",
                "online" if step["online"] else "offline",
                "%d validators -> %s"
                % (len(step["validators"]),
                   "online" if step["online"] else "offline"),
                len(step["validators"]), "validators")
        elif op == "set_binary":
            net.set_binary(step["validators"], step["has_new_binary"])
            res.update({"validators": step["validators"],
                        "has_new_binary": step["has_new_binary"]})
            row(op, "validators",
                "new-binary" if step["has_new_binary"]
                else "old-binary",
                "%d validators on %s binary"
                % (len(step["validators"]),
                   "new" if step["has_new_binary"] else "old"),
                len(step["validators"]), "validators")
        elif op == "rotate_manifest":
            seq = net.rotate_manifest(step["validator"])
            res.update({"validator": step["validator"],
                        "sequence": seq})
            row(op, step["validator"], "rotated",
                "new ephemeral key, sequence %d" % seq, seq,
                "sequence")
        elif op == "revoke_manifest":
            seq = net.revoke_manifest(step["validator"])
            res.update({"validator": step["validator"],
                        "sequence": seq})
            row(op, step["validator"], "revoked",
                "master key revoked, sequence 0xFFFFFFFF",
                seq, "sequence")
        elif op == "set_publisher":
            net.set_publisher(step["publisher"], step["available"])
            res.update({"publisher": step["publisher"],
                        "available": step["available"]})
            row(op, step["publisher"],
                "available" if step["available"] else "unavailable",
                "publisher %s -> %s"
                % (step["publisher"],
                   "available" if step["available"] else "unavailable"),
                1 if step["available"] else 0, "available")
        elif op == "mark_unreliable":
            net.mark_unreliable(step["validators"])
            res.update({"validators": step["validators"]})
            row(op, "validators", "marked-unreliable",
                "%d validators marked unreliable (negative UNL)"
                % len(step["validators"]), len(step["validators"]),
                "validators")
        elif op == "fee_votes":
            net.fee_votes(step["field"], step["distribution"])
            res.update({"field": step["field"],
                        "distribution": step["distribution"]})
            row(op, step["field"], "votes-cast",
                "votes %s" % step["distribution"],
                sum(step["distribution"].values()), "votes")
        elif op == "fee_target":
            net.fee_targets[step["field"]] = step["value"]
            res.update({"field": step["field"], "value": step["value"]})
            row(op, step["field"], "target-set",
                "operator target %s = %d"
                % (step["field"], step["value"]), step["value"],
                "drops")
        elif op == "exclusion_vote":
            ok = net.exclusion_vote(step["account"],
                                    step["agreeing"])
            res.update({"account": step["account"],
                        "agreeing": step["agreeing"],
                        "queued": ok})
            row(op, step["account"],
                "queued" if ok else "rejected",
                "%d validators agree to exclude %s"
                % (step["agreeing"], step["account"]),
                step["agreeing"], "validators")
        elif op == "majority_time_override":
            net.majority_time_override(step["minutes"])
            res.update({"minutes": step["minutes"]})
            row(op, "amendment_majority_time", "overridden",
                "majority hold set to %d minutes"
                % step["minutes"], step["minutes"], "minutes")
        elif op == "binary_upgrade":
            net.binary_upgrade(step["validators"])
            res.update({"validators": step["validators"]})
            row(op, "validators", "upgraded",
                "%d validators upgraded sequentially"
                % len(step["validators"]), len(step["validators"]),
                "validators")
        elif op == "rollback_attempt":
            ok = net.rollback_attempt(step["amendment"])
            res.update({"amendment": step["amendment"],
                        "rolled_back": ok})
            row(op, step["amendment"],
                "rolled-back" if ok else "failed",
                "no in-protocol rollback path" if not ok
                else "rolled back",
                1 if ok else 0, "attempts")
        elif op == "ledger_replay":
            n = net.ledger_replay(step["ledgers"])
            res.update({"ledgers": n})
            row(op, "replay", "replayed",
                "%d ledgers re-executed on one node; enabled "
                "amendments unchanged" % n, n, "ledgers")
        elif op == "advance":
            before = dict(net.counters)
            out = net.advance(step["days"])
            res.update(out)
            res.update({"day": round(net.day, 4),
                        "ledger_seq": net.ledger_seq})
            validated = (net.counters["ledgers_validated"]
                         - before["ledgers_validated"])
            missed = (net.counters["ledgers_missed"]
                      - before["ledgers_missed"])
            row(op, "ledgers",
                "validated" if missed == 0 else "missed",
                "%.4f days: quorum %s, online %d, validated %d, "
                "missed %d" % (step["days"], out["quorum"],
                               out["online"], validated, missed),
                validated, "ledgers")
            row(op, "flag-ledgers", "evaluated",
                "%d flag ledgers evaluated (doVoting + fee vote)"
                % out["flag_ledgers"], out["flag_ledgers"],
                "flag ledgers")
        else:
            raise ValueError("unknown op %r" % op)
        step_results.append(res)

    result = {
        "scenario_id": scen["id"],
        "title": scen["title"],
        "severity": scen["severity"],
        "severity_reason": scen["severity_reason"],
        "label": "SIMULATED",
        "pinned_commit": PINNED_COMMIT,
        "config": scen["config"],
        "steps": step_results,
        "rows": rows,
        "events": net.events,
        "final": net.final_state(),
    }
    return scen["id"], result, log, rows


def main(argv):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(base, "outputs")
    os.makedirs(outdir, exist_ok=True)
    for path in argv[1:]:
        sid, result, log, rows = run_scenario(path)
        json_path = os.path.join(outdir, sid + ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
        csv_path = os.path.join(outdir, sid + ".csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(rows)
        log_path = os.path.join(outdir, sid + ".log")
        with open(log_path, "w", encoding="utf-8") as f:
            for line in log:
                f.write(line + "\n")
        fin = result["final"]
        print("%s: %d rows, %d events, enabled %d, validated %d, "
              "missed %d, quorum %s"
              % (sid, len(rows), len(result["events"]),
                 fin["counters"]["amendments_enabled"],
                 fin["counters"]["ledgers_validated"],
                 fin["counters"]["ledgers_missed"],
                 fin["validation_quorum"]))


if __name__ == "__main__":
    main(sys.argv)
