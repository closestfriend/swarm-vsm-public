"""Freeze prefix and evidence-window inputs for the four-case Swarm Traces check.

Writes frozen_inputs.jsonl (holds corpus text, gitignored) and manifest.json
(offsets and hashes only). judge.py refuses to run if the frozen file changed.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from batch_classify_vsm import extract_forensic_metadata  # noqa: E402

HERE = Path(__file__).resolve().parent
BUDGET = 2400
GAP = "\n[...]\n"
CASES = {
    "R0189558": "dispatch_positive",
    "R0189562": "dispatch_positive",
    "R0189553": "direct_control",
    "R0189569": "direct_control",
}
# Manually verified dispatch call spans (dispatch_links.jsonl).
DISPATCH = {"R0189558": (4708, 4754), "R0189562": (4396, 4442)}
HEADER = 300  # keep the record banner (source file, command number)


def build_window(text, rid):
    """Return (window_text, segments) where segments are source (start, end) offsets."""
    if len(text) <= BUDGET:
        return text, [(0, len(text))]
    if rid not in DISPATCH:
        return text[:BUDGET], [(0, BUDGET)]
    s, e = DISPATCH[rid]
    # Segment A: banner. Segment B: the dispatch call with surrounding context,
    # which also carries the worker task definition and the later polling.
    remaining = BUDGET - HEADER - len(GAP)
    lo = max(HEADER, s - 700)
    hi = min(len(text), lo + remaining)
    if hi < e + 400:
        hi = min(len(text), e + 400)
    lo = max(HEADER, hi - remaining)  # spend any spare budget on preceding context
    return text[:HEADER] + GAP + text[lo:hi], [(0, HEADER), (lo, hi)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    args = ap.parse_args()
    rows = {}
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["id"] in CASES:
                rows[r["id"]] = r
    out, manifest = [], {"budget": BUDGET, "cases": {}}
    for rid, role in CASES.items():
        r = rows[rid]
        text = r.get("text") or ""
        meta = extract_forensic_metadata(r)
        window, segs = build_window(text, rid)
        prefix = text[:BUDGET]
        assert len(window) <= BUDGET and len(prefix) <= BUDGET
        shared = {
            "trace_id": rid, "kind": r.get("kind"), "parent_id": r.get("parent_id"),
            "tags": r.get("tags") or None, "source_agent_id": meta["agent_id"],
            "detected_targets": meta["targets"], "shared_artifacts": meta["shared_artifacts"],
            "embedded_timestamp": meta["embedded_timestamp"], "record_length": len(text),
        }
        for cond, excerpt, spans in (("prefix", prefix, [(0, len(prefix))]), ("window", window, segs)):
            out.append({"case": rid, "role": role, "condition": cond, "metadata": shared,
                        "excerpt": excerpt, "source_spans": spans})
        d = DISPATCH.get(rid)
        manifest["cases"][rid] = {
            "role": role, "record_length": len(text), "cite": r["cite"],
            "prefix_span": [0, len(prefix)], "window_spans": segs, "window_len": len(window),
            "dispatch_span_in_prefix": bool(d and d[1] <= len(prefix)),
            "dispatch_span_in_window": bool(d and any(a <= d[0] and d[1] <= b for a, b in segs)),
            "prefix_sha256": sha256(prefix.encode()).hexdigest(),
            "window_sha256": sha256(window.encode()).hexdigest(),
        }
    body = "".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out)
    (HERE / "frozen_inputs.jsonl").write_text(body, encoding="utf-8")
    manifest["frozen_inputs_sha256"] = sha256(body.encode()).hexdigest()
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
