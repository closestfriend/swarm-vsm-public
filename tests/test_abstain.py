"""Offline tests for the abstention option (no API calls; a fake client stands in).

Run from the swarm-vsm directory: .venv/bin/python -B tests/test_abstain.py
"""
import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import batch_classify_vsm as b  # noqa: E402
from schema import TraceAnnotation  # noqa: E402

ROW = {"id": "x" * 64, "text": "HELLO COORD TEST", "source_id": "dse/P", "site": "s", "title": "P",
       "origin_kind": "revision_addition", "date": "2026-06-01T00:00:00Z", "selection_basis": "b",
       "_episode_override": "page:dse/P"}
BASE = {"trace_id": "t", "turn_index": 0, "source_agent_id": "unresolved", "target_agent_ids": [],
        "reasoning_chain": "r", "primary_vsm": "S0_NOISE", "secondary_vsm": None,
        "cadence_mode": "ASYNCHRONOUS_SLOW", "variety_operator": "AMPLIFIER", "confidence": 0.2}


class FakeClient:
    def __init__(self, payload):
        self.calls = 0
        self.payload = payload
        self.responses = self

    async def create(self, **kw):
        self.calls += 1
        self.last_instructions = kw["instructions"]
        return type("R", (), {"output_text": json.dumps(self.payload)})()


def classify(payload):
    client = FakeClient(payload)
    ann = asyncio.run(b.classify_wiki_record(asyncio.Semaphore(1), client, dict(ROW), 0, "fake"))
    return ann, client


def test_default_mode_unchanged():
    b.configure_wiki(ROOT / "calibration" / "wiki_prompt.md", abstain=False)
    assert b.prompt_sha256("wiki").startswith("bef3bc698b4b"), "v1 prompt hash changed"
    ann, client = classify(BASE)
    assert ann.evidence_status is None and "evidence_status" not in client.last_instructions


def test_abstain_mode_requires_status():
    b.configure_wiki(ROOT / "calibration" / "wiki_prompt_v2.md", abstain=True)
    ann, client = classify(dict(BASE, evidence_status="insufficient_evidence"))
    assert ann.evidence_status == "insufficient_evidence" and client.calls == 1
    assert '"evidence_status"' in client.last_instructions
    try:
        classify(BASE)  # missing evidence_status -> retried, then fails
        raise AssertionError("missing evidence_status was accepted")
    except RuntimeError as exc:
        assert "evidence_status" in str(exc)
    b.configure_wiki(ROOT / "calibration" / "wiki_prompt.md", abstain=False)


def test_cohort_from_copies_ids_exactly():
    src = ROOT / "calibration" / "wiki_overnight" / "cohort.json"
    with tempfile.TemporaryDirectory() as d:
        b.configure_wiki(ROOT / "calibration" / "wiki_prompt_v2.md", abstain=True)
        a = argparse.Namespace(source="wiki", cohort_from=str(src), model="qwen3.5-397b")
        new = b.freeze_cohort(Path(d) / "cohort.json", Path("unused"), a)
        old = json.loads(src.read_text())
        assert new["records"] == old["records"] and len(new["records"]) == 6051
        assert new["config"]["abstain"] is True and new["config"]["wiki_prompt"] == "wiki_prompt_v2.md"
        assert new["config"]["prompt_sha256"] != old["config"]["prompt_sha256"]
        # reopening with the v1 prompt must be refused
        b.configure_wiki(ROOT / "calibration" / "wiki_prompt.md", abstain=False)
        try:
            b.freeze_cohort(Path(d) / "cohort.json", Path("unused"), argparse.Namespace(source="wiki"))
            raise AssertionError("prompt change was not refused")
        except SystemExit:
            pass


def test_compare_script():
    with tempfile.TemporaryDirectory() as d:
        rows1 = [dict(BASE, record_id=f"r{i}", primary_vsm=p, confidence=0.7)
                 for i, p in enumerate(["S2_COORDINATION", "S1_OPERATIONS", "S0_NOISE", "S2_COORDINATION"])]
        rows2 = [dict(r, evidence_status=s) for r, s in
                 zip(rows1, ["sufficient", "insufficient_evidence", "insufficient_evidence", "sufficient"])]
        for name, rows in (("v1.jsonl", rows1), ("v2.jsonl", rows2)):
            (Path(d) / name).write_text("".join(TraceAnnotation(**r).model_dump_json() + "\n" for r in rows))
        out = subprocess.run([sys.executable, "-B", str(ROOT / "calibration/wiki_abstain/compare.py"),
                              "--v1", f"{d}/v1.jsonl", "--v2", f"{d}/v2.jsonl"],
                             capture_output=True, text=True, check=True).stdout
        res = json.loads(out)
        assert res["abstained"] == 2 and res["agreement_on_sufficient"] == 1.0
        assert res["abstained_by_v1_label"]["S1_OPERATIONS"]["abstained"] == 1
        (ROOT / "calibration/wiki_abstain/comparison.json").unlink()  # test artefact


def test_swarm_default_unchanged_and_abstain():
    b.configure_swarm(None)
    assert b.swarm_instructions() == b.INSTRUCTIONS
    b.configure_swarm(ROOT / "calibration" / "swarm_prompt_v2.md", abstain=True)
    ins = b.swarm_instructions()
    assert '"evidence_status"' in ins and "Swarm Traces" in ins
    row = {"id": "R0000001", "kind": "payload", "parent_id": None, "tags": "", "text": "x"}
    client = FakeClient(dict(BASE, evidence_status="sufficient"))
    ann = asyncio.run(b.classify_record(asyncio.Semaphore(1), client, row, 0, "fake"))
    assert ann.evidence_status == "sufficient"
    try:
        asyncio.run(b.classify_record(asyncio.Semaphore(1), FakeClient(BASE), row, 0, "fake"))
        raise AssertionError("missing evidence_status was accepted")
    except RuntimeError:
        pass
    b.configure_swarm(None)


def test_swarm_stratified_sample():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "c.jsonl"
        kinds = ["payload"] * 50 + ["recovered_text"] * 40 + ["response"] * 10
        p.write_text("".join(json.dumps({"id": f"R{i:07d}", "kind": k, "parent_id": None, "tags": "",
                                         "text": "t"}) + "\n" for i, k in enumerate(kinds)))
        s1 = b.select_swarm_stratified(p, 20, 0)
        s2 = b.select_swarm_stratified(p, 20, 0)
        from collections import Counter
        c = Counter(r["kind"] for r in s1)
        assert [r["id"] for r in s1] == [r["id"] for r in s2], "not deterministic"
        assert c == {"payload": 10, "recovered_text": 8, "response": 2}, c
        assert [r["id"] for r in s1] == sorted(r["id"] for r in s1)


if __name__ == "__main__":
    test_swarm_default_unchanged_and_abstain()
    test_swarm_stratified_sample()
    test_default_mode_unchanged()
    test_abstain_mode_requires_status()
    test_cohort_from_copies_ids_exactly()
    test_compare_script()
    print("ok")
