"""Offline tests for the resumable runner using a fake classifier (no API calls).

Run from the swarm-vsm directory: .venv/bin/python -B -m pytest tests -q
(or: .venv/bin/python -B tests/test_resume.py)
"""
import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import batch_classify_vsm as b  # noqa: E402
from schema import CadenceMode, TraceAnnotation, VarietyOperator, VSMSystem  # noqa: E402
from verify_batch_output import verify  # noqa: E402

N = 12


def make_corpus(path):
    with open(path, "w") as f:
        for i in range(N):
            f.write(json.dumps({"id": f"R{i:07d}", "cite": f"R{i:07d}:x", "kind": "payload",
                                "parent_id": None, "tags": "", "text": f"echo {i}"}) + "\n")


def args_for(tmp, **kw):
    ns = dict(input=str(tmp / "c.jsonl"), pilot_dir=str(tmp / "pilot"), episodes=None, limit=N,
              payload_sample=N, dag_children=0, model="fake", concurrency=3, stop_after=0)
    ns.update(kw)
    return argparse.Namespace(**ns)


def make_fake(calls, fail_ids=()):
    async def fake(sem, client, row, turn_index, model):
        calls.append(row["id"])
        if row["id"] in fail_ids:
            raise RuntimeError("boom")
        await asyncio.sleep(0.01)
        return TraceAnnotation(
            trace_id=row["id"], turn_index=turn_index, source_agent_id="a", target_agent_ids=[],
            reasoning_chain="r", primary_vsm=VSMSystem.S1_OPERATIONS, cadence_mode=CadenceMode.SYNCHRONOUS_FAST,
            variety_operator=VarietyOperator.AMPLIFIER, confidence=0.5, record_id=row["id"],
            episode_id="wrong", )
    return fake


def run(a, fake):
    return asyncio.run(b.run_resumable(a, classify=fake))


def test_interrupt_resume_skips_done_and_retries_failed():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        make_corpus(tmp / "c.jsonl")
        calls1: list = []
        assert run(args_for(tmp, stop_after=5), make_fake(calls1)) == 3
        pilot = tmp / "pilot"
        first = {json.loads(l)["record_id"] for l in (pilot / "results.jsonl").read_text().splitlines()}
        assert len(first) >= 5
        # restart with one ID failing: it stays missing and eligible
        calls2: list = []
        bad = "R0000011"  # last cohort ID; not among the first five completed
        assert run(args_for(tmp), make_fake(calls2, fail_ids={bad})) == 2
        assert not (set(calls2) & first), "completed IDs were resubmitted"
        assert (pilot / "failures.jsonl").exists()
        # restart again, failure cleared: only the failed ID is submitted
        calls3: list = []
        assert run(args_for(tmp), make_fake(calls3)) == 0
        assert calls3 == [bad]
        rep = verify(pilot, "final.jsonl")
        assert rep["ok"], rep
        assert rep["valid_rows"] == N and rep["completed_ids_resubmitted"] == []


def test_torn_trailing_line_is_resubmitted_and_frozen_assignments_hold():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        make_corpus(tmp / "c.jsonl")
        assert run(args_for(tmp, stop_after=4), make_fake([])) == 3
        pilot = tmp / "pilot"
        cohort_before = (pilot / "cohort.json").read_text()
        lines = (pilot / "results.jsonl").read_text().splitlines()
        torn_id = json.loads(lines[-1])["record_id"]
        (pilot / "results.jsonl").write_text("\n".join(lines[:-1]) + "\n" + lines[-1][:30])
        calls: list = []
        # different selection args on restart must not change the frozen cohort
        assert run(args_for(tmp, limit=3), make_fake(calls)) == 0
        assert torn_id in calls
        assert (pilot / "cohort.json").read_text() == cohort_before
        assert verify(pilot, "results.jsonl")["problems"] == []


if __name__ == "__main__":
    test_interrupt_resume_skips_done_and_retries_failed()
    test_torn_trailing_line_is_resubmitted_and_frozen_assignments_hold()
    print("ok")
