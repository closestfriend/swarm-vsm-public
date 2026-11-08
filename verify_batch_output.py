"""Verify a resumable pilot directory: exactly one schema-valid row per frozen cohort ID.

Usage: python verify_batch_output.py PILOT_DIR [--file results.jsonl|final.jsonl]
Exit 0 only if there are zero gaps, duplicates, strays, invalid rows, or changed
episode/turn assignments. Also reports restart evidence from run_log.jsonl.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from schema import TraceAnnotation


def verify(pilot: Path, name: str) -> dict:
    cohort = json.loads((pilot / "cohort.json").read_text(encoding="utf-8"))
    expected = {e["id"]: e for e in cohort["records"]}
    path = pilot / name
    report = {"file": str(path), "cohort_size": len(expected), "problems": []}
    ids, invalid = [], 0
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            ann = TraceAnnotation.model_validate_json(line)
        except Exception as exc:  # noqa: BLE001
            invalid += 1
            report["problems"].append(f"line {n}: schema invalid ({type(exc).__name__})")
            continue
        ids.append(ann.record_id)
        e = expected.get(ann.record_id)
        if e and (ann.episode_id != e["episode_id"] or ann.turn_index != e["turn_index"]):
            report["problems"].append(f"{ann.record_id}: episode/turn differs from frozen cohort")
    counts = Counter(ids)
    report["rows"] = len(ids) + invalid
    report["valid_rows"] = len(ids)
    report["duplicates"] = sorted(i for i, c in counts.items() if c > 1)
    report["gaps"] = sorted(set(expected) - set(counts))
    report["strays"] = sorted(set(counts) - set(expected))
    for key in ("duplicates", "gaps", "strays"):
        if report[key]:
            report["problems"].append(f"{key}: {report[key][:5]}")

    # Restart evidence. Each run_start records which IDs were already durably in results.jsonl
    # (skipped_completed) and which it submitted. Per run: the two sets must be disjoint and
    # together cover the cohort. Across runs: a result may be written for an ID only once, and
    # a later run may not submit an ID an earlier run wrote unless a torn write was repaired.
    runs, resubmitted, written_by = 0, [], {}
    prev_skipped, repaired = set(), False
    log = pilot / "run_log.jsonl"
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            ev = json.loads(line)
            if ev["event"] == "repaired_torn_tail":
                repaired = True
            elif ev["event"] == "run_start":
                runs += 1
                skipped, submitting = set(ev["skipped_completed"]), set(ev["submitting"])
                if skipped & submitting:
                    resubmitted += sorted(skipped & submitting)
                if skipped | submitting != set(expected) or skipped & submitting:
                    report["problems"].append(f"run {runs}: skipped/submitting do not partition the cohort")
                lost = sorted(prev_skipped - skipped)
                if lost:
                    report["problems"].append(f"run {runs}: previously completed IDs vanished: {lost[:5]}")
                for rid in sorted(set(written_by) & submitting):
                    if not repaired:
                        resubmitted.append(rid)
                        report["problems"].append(f"run {runs}: resubmitted {rid} written in run {written_by[rid]}")
                prev_skipped, repaired = skipped, False
            elif ev["event"] == "result":
                written_by[ev["id"]] = runs
    report["runs"] = runs
    report["completed_ids_resubmitted"] = sorted(set(resubmitted))
    report["ok"] = not report["problems"]
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pilot_dir", type=Path)
    ap.add_argument("--file", default="final.jsonl")
    a = ap.parse_args()
    rep = verify(a.pilot_dir, a.file)
    print(json.dumps(rep, indent=2))
    raise SystemExit(0 if rep["ok"] else 1)
