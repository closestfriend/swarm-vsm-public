import argparse
import asyncio
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from adaption import Adaption, AsyncAdaption
from schema import CadenceMode, RecordKind, TraceAnnotation, VarietyOperator, VSMSystem


def ensure_api_key() -> None:
    if os.environ.get("ADAPTION_API_KEY"):
        return
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        match = re.search(
            r'export\s+ADAPTION_API_KEY=["\']?([^"\'\s]+)["\']?',
            zshrc.read_text(encoding="utf-8", errors="ignore"),
        )
        if match:
            os.environ["ADAPTION_API_KEY"] = match.group(1)


CORE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "trace_id": {"type": "string"},
        "turn_index": {"type": "integer"},
        "source_agent_id": {"type": "string"},
        "target_agent_ids": {"type": "array", "items": {"type": "string"}},
        "reasoning_chain": {"type": "string"},
        "primary_vsm": {"type": "string", "enum": [e.value for e in VSMSystem]},
        "secondary_vsm": {
            "anyOf": [
                {"type": "string", "enum": [e.value for e in VSMSystem]},
                {"type": "null"},
            ]
        },
        "cadence_mode": {"type": "string", "enum": [e.value for e in CadenceMode]},
        "variety_operator": {"type": "string", "enum": [e.value for e in VarietyOperator]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
    "required": [
        "trace_id",
        "turn_index",
        "source_agent_id",
        "target_agent_ids",
        "reasoning_chain",
        "primary_vsm",
        "secondary_vsm",
        "cadence_mode",
        "variety_operator",
        "confidence",
    ],
}

INSTRUCTIONS = f"""You are a cybernetic forensics classifier mapping multi-agent telemetry traces into Stafford Beer's Viable System Model (VSM) and Ashby's Law of Requisite Variety.

Classify each trace record strictly by its operational mechanics:
- S0_NOISE: Unstructured noise, empty redirects, or non-operational chatter.
- S1_OPERATIONS: Direct atomic tool/task execution (submitting code, shell execution, direct exploit payload delivery, HTTP data fetch).
- S2_COORDINATION: Anti-oscillation, shared filesystem boards (/tmp/g236_tokens.json, /tmp/g236sharedone.py, /tmp/sres), lockfiles, status ledgers, polling task queues, or durable shared-infra bridges.
- S3_CONTROL: Vertical task allocation, splitting goals into sub-tasks, spawning child controllers, or delegating across worker nodes.
- S3_STAR_AUDIT: Sporadic unmediated verification, checksums, signature verification, diffs, health/noop checks, or abort triggers.
- S4_INTELLIGENCE: Environmental recon (id, uname -a, hostname, /proc/1/status, k8s API discovery, IMDS credential probing, port scanning, Slack/GitHub/CVE search), boundary/filter probing.
- S5_POLICY: Global doctrine, stealth posture, alias/lineage closure, causal wrapper layers.

CadenceMode:
- SYNCHRONOUS_FAST: Immediate blocking request/response or direct command execution.
- ASYNCHRONOUS_SLOW: Polling, deferred execution, token refresh loops, or background queue/shared-file coordination.
- BROADCAST_STATE: Emitting state/beacons to shared channels, external listeners, or multi-host sweeps.

VarietyOperator:
- AMPLIFIER: Expands state/options, probes environment, scans hosts/ports, spawns commands, or broadcasts payloads.
- ATTENUATOR: Filters, constrains, locks, verifies checksums/signatures, summarizes state, or executes noop damping.

Respond ONLY with a valid JSON object matching this exact schema (no markdown fences, no extra prose):
{json.dumps(CORE_JSON_SCHEMA, indent=2)}
"""


def extract_forensic_metadata(row: dict) -> dict:
    """Deterministic extraction of embedded fields, shared artifacts, and temporal markers."""
    text = row.get("text") or ""
    tags = row.get("tags") or ""
    extracted: dict = {}

    for key in ("agent_id", "task_id", "function_name", "file_path", "checksum", "submitted_code"):
        pattern = rf'\\?"{key}\\?"\s*:\s*(?:\\?"([^"\\]*)\\?"|(null))'
        m = re.search(pattern, text)
        if m:
            extracted[key] = None if m.group(2) == "null" else m.group(1)

    # Identify source agent / credential / binary
    agent_id = extracted.get("agent_id")
    if not agent_id:
        if "g23619scmd.bin" in tags or "g23619scmd.bin" in text:
            agent_id = "g23619scmd.bin"
        elif "g23619cmd.bin" in tags or "g23619cmd.bin" in text:
            agent_id = "g23619cmd.bin"
        elif "g236-child-controller" in tags:
            agent_id = "g236-child-controller"
        elif "PHASEONE64H" in tags or "PHASEONE64H" in text:
            agent_id = "PHASEONE64H"
        else:
            cred_m = re.search(r"\[(CREDENTIAL\s+\d+|REDACTED:runtime_identifier(?::\d+)?)\]", text)
            agent_id = f"[{cred_m.group(1)}]" if cred_m else f"agent:{row.get('kind', 'unknown')}"

    # Identify shared filesystem boards, lockfiles, repos, and target hosts
    shared_artifacts = sorted(
        set(
            re.findall(
                r"(?:/tmp/[a-zA-Z0-9_.-]+|/var/run/secrets/[a-zA-Z0-9_./-]+|\[HF REPO \d+\])",
                text,
            )
        )
    )
    targets = sorted(
        set(
            re.findall(
                r"\[(?:REDACTED:destination:\d+|SERVICE \d+ URL \d+|INTERNAL HOST \d+|IP ADDRESS \d+|HF REPO \d+)\]",
                text,
            )
        )
    )

    # Extract embedded timestamp or sequence marker
    embedded_ts: Optional[str] = None
    iso_m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", text)
    cmd_m = re.search(r"command[- ](\d{6})", tags + " " + text)
    if iso_m:
        embedded_ts = iso_m.group(0)
    elif cmd_m:
        embedded_ts = f"cmd_seq:{cmd_m.group(1)}"
    elif "time.time()" in text:
        embedded_ts = "runtime:time.time()"

    # Determine logical episode ID
    if "g23619cmd.bin" in tags:
        episode_id = "episode:g23619cmd"
    elif "g23619scmd.bin" in tags:
        episode_id = "episode:g23619scmd"
    elif "slack-search" in tags:
        episode_id = "episode:slack-search"
    elif "article-evidence" in tags:
        episode_id = "episode:article-evidence"
    elif row.get("parent_id"):
        episode_id = f"dag:{row['parent_id']}"
    else:
        episode_id = f"stream:{agent_id}"

    return {
        "agent_id": agent_id,
        "task_id": extracted.get("task_id"),
        "function_name": extracted.get("function_name"),
        "file_path": extracted.get("file_path"),
        "checksum": extracted.get("checksum"),
        "shared_artifacts": shared_artifacts,
        "targets": targets,
        "embedded_timestamp": embedded_ts,
        "episode_id": episode_id,
    }


def strip_markdown_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Extract first balanced JSON object if model prepended/appended commentary
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def resolve_input_path(custom_path: Optional[str] = None) -> Path:
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
    for candidate in (
        Path("../redacted.jsonl"),
        Path("./redacted.jsonl"),
        Path(__file__).resolve().parent.parent / "redacted.jsonl",
    ):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not locate redacted.jsonl")


def select_stratified_cohort(input_path: Path, payload_sample: int = 15, dag_children_per_tree: int = 3) -> list[dict]:
    """
    Selects a stratified temporal & causal cohort from redacted.jsonl:
      1. Initial sequential payload stream (turns 0..payload_sample-1)
      2. Causal parent->child DAG episodes (root payload + response + recovered_text children)
      3. All 37 tagged forensic `article-evidence` records (g23619cmd.bin, g23619scmd.bin, child controller, slack-search, etc.)
    """
    payload_stream: list[dict] = []
    tagged_records: list[dict] = []
    target_roots = {"R0000027", "R0024455", "R0189559"}
    roots_by_id: dict[str, dict] = {}
    children_by_parent: dict[str, list[dict]] = defaultdict(list)

    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            rid = row["id"]
            pid = row.get("parent_id")

            if i < payload_sample:
                row["_episode_override"] = "episode:initial_payload_stream"
                payload_stream.append(row)

            if rid in target_roots:
                roots_by_id[rid] = row

            if pid in target_roots and len(children_by_parent[pid]) < dag_children_per_tree:
                children_by_parent[pid].append(row)

            if row.get("tags"):
                tagged_records.append(row)

    cohort: list[dict] = []
    seen_ids: set[str] = set()

    def add_row(r: dict, ep_override: Optional[str] = None) -> None:
        if r["id"] not in seen_ids:
            if ep_override:
                r = dict(r)
                r["_episode_override"] = ep_override
            cohort.append(r)
            seen_ids.add(r["id"])

    for r in payload_stream:
        add_row(r, "episode:initial_payload_stream")

    for root_id in ("R0000027", "R0024455"):
        if root_id in roots_by_id:
            add_row(roots_by_id[root_id], f"dag:{root_id}")
            for child in children_by_parent[root_id]:
                add_row(child, f"dag:{root_id}")

    for r in tagged_records:
        add_row(r)

    return cohort


async def classify_record(
    sem: asyncio.Semaphore,
    client: AsyncAdaption,
    row: dict,
    turn_index: int,
    model: str,
) -> TraceAnnotation:
    meta = extract_forensic_metadata(row)
    record_id = str(row.get("id") or f"trace_{turn_index}")
    episode_id = row.get("_episode_override") or meta["episode_id"]

    prompt_context = {
        "trace_id": record_id,
        "turn_index": turn_index,
        "episode_id": episode_id,
        "kind": row.get("kind"),
        "parent_id": row.get("parent_id"),
        "tags": row.get("tags") or None,
        "source_agent_id": meta["agent_id"],
        "detected_targets": meta["targets"],
        "shared_artifacts": meta["shared_artifacts"],
        "embedded_timestamp": meta["embedded_timestamp"],
        "task_id": meta["task_id"],
        "function_name": meta["function_name"],
        "file_path": meta["file_path"],
        "checksum": meta["checksum"],
        "raw_text_excerpt": (row.get("text") or "")[:2400],
    }

    user_input = (
        f"Classify this cybernetic trace turn (trace_id={record_id}, turn_index={turn_index}, "
        f"source_agent_id={meta['agent_id']}):\n"
        f"{json.dumps(prompt_context, indent=2)}"
    )

    async with sem:
        for attempt in range(3):
            try:
                response = await client.responses.create(
                    model=model,
                    instructions=swarm_instructions(),
                    input=user_input,
                    temperature=0.0,
                )
                cleaned = strip_markdown_fences(response.output_text)
                ann = TraceAnnotation.model_validate_json(cleaned)
                if SWARM_PROMPT_PATH and WIKI_ABSTAIN and ann.evidence_status is None:
                    raise ValueError("evidence_status missing in abstention mode")
                break
            except Exception as exc:
                if attempt == 2:
                    raise RuntimeError(f"Failed on record {record_id}: {exc}") from exc
                await asyncio.sleep(1.5 * (attempt + 1))

    # Populate deterministic forensic & topological fields on the validated model
    ann.trace_id = record_id
    ann.turn_index = turn_index
    ann.record_id = record_id
    ann.parent_id = row.get("parent_id")
    ann.episode_id = episode_id
    if row.get("kind") in {k.value for k in RecordKind}:
        ann.record_kind = RecordKind(row["kind"])
    ann.tags = row.get("tags") or None
    ann.embedded_timestamp = meta["embedded_timestamp"]
    ann.shared_artifacts = meta["shared_artifacts"]
    if not ann.target_agent_ids and meta["targets"]:
        ann.target_agent_ids = meta["targets"]

    return ann


def compute_markov_analytics(annotations: list[TraceAnnotation]) -> dict:
    """
    Computes:
      1. State distribution across VSM systems, CadenceMode, VarietyOperator
      2. Sequential transition matrix P(S_{t+1} | S_t) within each episode trajectory
      3. Causal DAG transition matrix P(S_child | S_parent) across parent_id links
    """
    vsm_counts = Counter(a.primary_vsm.value for a in annotations)
    cadence_counts = Counter(a.cadence_mode.value for a in annotations)
    variety_counts = Counter(a.variety_operator.value for a in annotations)

    # Group by episode_id preserving turn_index order
    by_episode: dict[str, list[TraceAnnotation]] = defaultdict(list)
    by_record_id: dict[str, TraceAnnotation] = {}
    for a in annotations:
        by_episode[a.episode_id or "default"].append(a)
        if a.record_id:
            by_record_id[a.record_id] = a

    seq_transitions: dict[str, Counter] = defaultdict(Counter)
    for ep_id, turns in by_episode.items():
        ordered = sorted(turns, key=lambda x: x.turn_index)
        for i in range(len(ordered) - 1):
            s_t = ordered[i].primary_vsm.value
            s_next = ordered[i + 1].primary_vsm.value
            seq_transitions[s_t][s_next] += 1

    # Normalize P(S_{t+1} | S_t)
    seq_prob_matrix: dict[str, dict[str, float]] = {}
    for s_t, counter in sorted(seq_transitions.items()):
        total = sum(counter.values())
        seq_prob_matrix[s_t] = {
            s_next: round(cnt / total, 4) for s_next, cnt in sorted(counter.items())
        }

    # Causal parent -> child transitions
    causal_transitions: dict[str, Counter] = defaultdict(Counter)
    for a in annotations:
        if a.parent_id and a.parent_id in by_record_id:
            p_vsm = by_record_id[a.parent_id].primary_vsm.value
            c_vsm = a.primary_vsm.value
            causal_transitions[p_vsm][c_vsm] += 1

    causal_prob_matrix: dict[str, dict[str, float]] = {}
    for p_vsm, counter in sorted(causal_transitions.items()):
        total = sum(counter.values())
        causal_prob_matrix[p_vsm] = {
            c_vsm: round(cnt / total, 4) for c_vsm, cnt in sorted(counter.items())
        }

    # Amplify / Attenuate ratio
    amp = variety_counts.get(VarietyOperator.AMPLIFIER.value, 0)
    att = variety_counts.get(VarietyOperator.ATTENUATOR.value, 0)

    return {
        "total_classified": len(annotations),
        "vsm_distribution": dict(vsm_counts),
        "cadence_distribution": dict(cadence_counts),
        "variety_distribution": dict(variety_counts),
        "amplifier_to_attenuator_ratio": round(amp / max(att, 1), 3),
        "sequential_transition_counts": {k: dict(v) for k, v in sorted(seq_transitions.items())},
        "sequential_transition_probabilities": seq_prob_matrix,
        "causal_dag_transition_counts": {k: dict(v) for k, v in sorted(causal_transitions.items())},
        "causal_dag_transition_probabilities": causal_prob_matrix,
    }


def print_summary(annotations: list[TraceAnnotation], analytics: dict) -> None:
    header = (
        f"{'Turn':<4} | {'Record ID':<9} | {'Parent':<9} | {'Episode':<24} | "
        f"{'Source Agent':<22} | {'Primary VSM':<15} | {'Secondary VSM':<15} | "
        f"{'Cadence':<17} | {'Variety':<10} | {'Conf':<4}"
    )
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    for a in annotations:
        sec = a.secondary_vsm.value if a.secondary_vsm else "-"
        pid = a.parent_id or "-"
        ep = (a.episode_id or "-")[:24]
        src = a.source_agent_id[:22]
        print(
            f"{a.turn_index:<4} | {a.trace_id:<9} | {pid:<9} | {ep:<24} | "
            f"{src:<22} | {a.primary_vsm.value:<15} | {sec:<15} | "
            f"{a.cadence_mode.value:<17} | {a.variety_operator.value:<10} | {a.confidence:<4.2f}"
        )
    print("=" * len(header))

    print("\n[1] VSM System Distribution:")
    for k, v in sorted(analytics["vsm_distribution"].items()):
        pct = 100.0 * v / max(analytics["total_classified"], 1)
        print(f"    {k:<18}: {v:>4} ({pct:5.1f}%)")

    print("\n[2] Cadence & Variety Balance:")
    for k, v in sorted(analytics["cadence_distribution"].items()):
        print(f"    Cadence {k:<18}: {v:>4}")
    for k, v in sorted(analytics["variety_distribution"].items()):
        print(f"    Variety {k:<18}: {v:>4}")
    print(f"    Amplifier/Attenuator Ratio: {analytics['amplifier_to_attenuator_ratio']}")

    print("\n[3] Sequential Markov Transition Matrix P(S_{t+1} | S_t):")
    for s_t, probs in analytics["sequential_transition_probabilities"].items():
        transitions_str = ", ".join(f"{s_next}: {p:.2f}" for s_next, p in probs.items())
        print(f"    {s_t:<18} -> {{ {transitions_str} }}")

    if analytics["causal_dag_transition_probabilities"]:
        print("\n[4] Causal DAG Transition Matrix P(S_child | S_parent):")
        for p_vsm, probs in analytics["causal_dag_transition_probabilities"].items():
            transitions_str = ", ".join(f"{c_vsm}: {p:.2f}" for c_vsm, p in probs.items())
            print(f"    {p_vsm:<18} -> {{ {transitions_str} }}")


# ---------------------------------------------------------------------------
# Resumable pilot mode (--pilot-dir). Separate from the legacy run_batch outputs.
#   cohort.json    frozen cohort: ordered IDs with episode_id and turn_index
#   results.jsonl  append-only, one validated TraceAnnotation per canonical record ID
#   failures.jsonl failed attempts (IDs stay eligible for retry)
#   run_log.jsonl  per-run config, skipped/submitted IDs, per-result latency, throughput
# ---------------------------------------------------------------------------
PILOT_DEFAULT_EPISODES = (
    "episode:initial_payload_stream",
    "dag:R0000027",
    "dag:R0024455",
    "episode:slack-search",
    "episode:g23619scmd",
    "episode:g23619cmd",
)


def row_episode(row: dict) -> str:
    return row.get("_episode_override") or extract_forensic_metadata(row)["episode_id"]


# ---------------------------------------------------------------------------
# Wiki agent-text records (records.jsonl.gz). Episode = first origin's source page;
# turns ordered by the origin's source date. Only dated records are used.
# ---------------------------------------------------------------------------
WIKI_PROMPT_PATH = Path(__file__).resolve().parent / "calibration" / "wiki_prompt.md"
WIKI_ABSTAIN = False  # set by configure_wiki(); True requires evidence_status in every answer


def configure_wiki(prompt_path=None, abstain: bool = False) -> None:
    global WIKI_PROMPT_PATH, WIKI_ABSTAIN
    if prompt_path:
        WIKI_PROMPT_PATH = Path(prompt_path).resolve()
    WIKI_ABSTAIN = abstain


def wiki_json_schema() -> dict:
    if not WIKI_ABSTAIN:
        return CORE_JSON_SCHEMA
    schema = json.loads(json.dumps(CORE_JSON_SCHEMA))
    schema["properties"]["evidence_status"] = {
        "type": "string", "enum": ["sufficient", "insufficient_evidence"]}
    schema["required"].append("evidence_status")
    return schema


def wiki_instructions() -> str:
    return (
        WIKI_PROMPT_PATH.read_text(encoding="utf-8")
        + "\nRespond ONLY with a valid JSON object matching this exact schema "
        "(no markdown fences, no extra prose):\n"
        + json.dumps(wiki_json_schema(), indent=2)
    )


# Swarm Traces prompt override. None keeps the original INSTRUCTIONS (all earlier runs).
# WIKI_ABSTAIN doubles as the abstention flag for this path.
SWARM_PROMPT_PATH = None


def configure_swarm(prompt_path=None, abstain: bool = False) -> None:
    global SWARM_PROMPT_PATH, WIKI_ABSTAIN
    SWARM_PROMPT_PATH = Path(prompt_path).resolve() if prompt_path else None
    WIKI_ABSTAIN = abstain if prompt_path else False


def swarm_instructions() -> str:
    if SWARM_PROMPT_PATH is None:
        return INSTRUCTIONS
    return (
        SWARM_PROMPT_PATH.read_text(encoding="utf-8")
        + "\nRespond ONLY with a valid JSON object matching this exact schema "
        "(no markdown fences, no extra prose):\n"
        + json.dumps(wiki_json_schema(), indent=2)
    )


def select_swarm_stratified(input_path: Path, n: int, seed: int) -> list:
    """Stratified random sample of Swarm Traces, proportional to record kind, deterministic:
    within each kind, take the first records by sha256(seed:id). Returned in ID order."""
    from hashlib import sha256

    by_kind: dict = defaultdict(list)
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            by_kind[r["kind"]].append(r)
    total = sum(len(v) for v in by_kind.values())
    quotas = {k: round(n * len(v) / total) for k, v in by_kind.items()}
    out = []
    for k, rows in by_kind.items():
        rows.sort(key=lambda r: sha256(f"{seed}:{r['id']}".encode()).hexdigest())
        out.extend(rows[: quotas[k]])
    return sorted(out, key=lambda r: r["id"])


def load_wiki_records(path: Path) -> dict:
    import gzip

    opener = gzip.open if str(path).endswith(".gz") else open
    rows = {}
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            o = (r.get("origins") or [{}])[0]
            rows[r["id"]] = {
                "id": r["id"],
                "text": r.get("text") or "",
                "source_id": o.get("source_id"),
                "site": o.get("site"),
                "title": o.get("title"),
                "origin_kind": o.get("kind"),
                "date": o.get("source_date_literal") or None,
                "n_origins": len(r.get("origins") or []),
                "selection_basis": r.get("selection_basis"),
                "body_withheld": r.get("body_withheld"),
            }
    return rows


def select_wiki_cohort(path: Path, min_per_page: int, cap: int, max_pages: int) -> list:
    """Dated records on pages with >= min_per_page dated records, first `cap` per page by date.
    max_pages > 0 keeps a deterministic pseudo-random subset of pages (by sha256 of page ID)."""
    from hashlib import sha256

    by_page: dict = defaultdict(list)
    for r in load_wiki_records(path).values():
        if r["date"] and r["source_id"]:
            by_page[r["source_id"]].append(r)
    pages = sorted(p for p, rs in by_page.items() if len(rs) >= min_per_page)
    if max_pages:
        pages = sorted(pages, key=lambda p: sha256(p.encode()).hexdigest())[:max_pages]
        pages.sort()
    out = []
    for p in pages:
        for r in sorted(by_page[p], key=lambda x: (x["date"], x["id"]))[:cap]:
            r = dict(r)
            r["_episode_override"] = f"page:{p}"
            out.append(r)
    return out


async def classify_wiki_record(
    sem: asyncio.Semaphore, client: AsyncAdaption, row: dict, turn_index: int, model: str
) -> TraceAnnotation:
    record_id = row["id"]
    episode_id = row["_episode_override"] if "_episode_override" in row else f"page:{row['source_id']}"
    text = row["text"]
    context = {
        "trace_id": record_id,
        "turn_index": turn_index,
        "episode_id": episode_id,
        "site": row["site"],
        "page_title": row["title"],
        "origin_kind": row["origin_kind"],
        "source_date": row["date"],
        "selection_basis": row["selection_basis"],
        "text_length": len(text),
        "text_excerpt": text[:2400],
    }
    user_input = f"Classify this record (trace_id={record_id}, turn_index={turn_index}):\n" + json.dumps(
        context, indent=2, ensure_ascii=False
    )
    instructions = wiki_instructions()
    async with sem:
        for attempt in range(3):
            try:
                response = await client.responses.create(
                    model=model, instructions=instructions, input=user_input, temperature=0.0
                )
                ann = TraceAnnotation.model_validate_json(strip_markdown_fences(response.output_text))
                if WIKI_ABSTAIN and ann.evidence_status is None:
                    raise ValueError("evidence_status missing in abstention mode")
                break
            except Exception as exc:
                if attempt == 2:
                    raise RuntimeError(f"Failed on record {record_id}: {exc}") from exc
                await asyncio.sleep(1.5 * (attempt + 1))
    ann.trace_id = record_id
    ann.record_id = record_id
    ann.turn_index = turn_index
    ann.parent_id = None
    ann.episode_id = episode_id
    ann.record_kind = None
    ann.tags = f"wiki;{row['site']};{row['origin_kind']}"
    ann.embedded_timestamp = row["date"]
    ann.shared_artifacts = [f"wiki-page:{row['source_id']}"]  # candidate channel, not proof of shared use
    return ann


def freeze_cohort(cohort_path: Path, input_path: Path, args: argparse.Namespace) -> dict:
    """Load the frozen cohort, or select and write it once. Never reselects if the file exists."""
    source = getattr(args, "source", "swarm")
    prompt_sha = prompt_sha256(source)
    if cohort_path.exists():
        cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
        cfg = cohort["config"]
        if cfg.get("source", "swarm") != source:
            raise SystemExit(f"cohort was frozen for source={cfg.get('source', 'swarm')}, not {source}")
        if cfg.get("prompt_sha256") and cfg["prompt_sha256"] != prompt_sha:
            raise SystemExit("prompt changed since this cohort was frozen; use a new --pilot-dir")
        return cohort
    cohort_from = getattr(args, "cohort_from", None)
    if cohort_from:
        # Reuse another run's frozen IDs, episodes and turns exactly; only the config is new.
        src = json.loads(Path(cohort_from).read_text(encoding="utf-8"))
        if src["config"].get("source", "swarm") != source:
            raise SystemExit(f"--cohort-from is a {src['config'].get('source', 'swarm')} cohort, not {source}")
        cohort = {
            "config": dict(src["config"], prompt_sha256=prompt_sha, model=args.model,
                           cohort_from=str(cohort_from),
                           cohort_from_prompt_sha256=src["config"].get("prompt_sha256"),
                           wiki_prompt=WIKI_PROMPT_PATH.name if source == "wiki" else None,
                           abstain=WIKI_ABSTAIN if source == "wiki" else None),
            "episode_counts": src["episode_counts"],
            "records": src["records"],
        }
        cohort_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cohort_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cohort, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, cohort_path)
        return cohort
    if source == "wiki":
        rows = select_wiki_cohort(input_path, args.wiki_min_per_page, args.wiki_cap, args.wiki_pages)
        wanted = None
    elif getattr(args, "swarm_cohort", "legacy") == "stratified":
        rows = select_swarm_stratified(input_path, args.swarm_n, args.seed)
        wanted = None
    else:
        rows = select_stratified_cohort(
            input_path, payload_sample=args.payload_sample, dag_children_per_tree=args.dag_children
        )
        wanted = args.episodes.split(",") if args.episodes else list(PILOT_DEFAULT_EPISODES)
        rows = [r for r in rows if row_episode(r) in wanted]
    if args.limit and len(rows) > args.limit:
        rows = rows[: args.limit]
    counters: Counter = Counter()
    entries = []
    for r in rows:
        ep = row_episode(r)
        entries.append({"id": r["id"], "episode_id": ep, "turn_index": counters[ep]})
        counters[ep] += 1
    cohort = {
        "config": {
            "source": source, "input": str(input_path), "prompt_sha256": prompt_sha,
            "episodes": wanted, "payload_sample": args.payload_sample,
            "dag_children": args.dag_children, "limit": args.limit, "model": args.model,
            **({"wiki_min_per_page": args.wiki_min_per_page, "wiki_cap": args.wiki_cap,
                "wiki_pages": args.wiki_pages, "wiki_prompt": WIKI_PROMPT_PATH.name,
                "abstain": WIKI_ABSTAIN} if source == "wiki" else {}),
            **({"swarm_cohort": "stratified", "swarm_n": args.swarm_n, "seed": args.seed,
                "swarm_prompt": SWARM_PROMPT_PATH.name if SWARM_PROMPT_PATH else None,
                "abstain": WIKI_ABSTAIN,
                "turn_order": "record ID order within heuristic episode; not time order"}
               if source == "swarm" and getattr(args, "swarm_cohort", "legacy") == "stratified" else {}),
        },
        "episode_counts": dict(counters),
        "records": entries,
    }
    cohort_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cohort_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cohort, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, cohort_path)
    return cohort


def prompt_sha256(source: str) -> str:
    from hashlib import sha256

    return sha256((wiki_instructions() if source == "wiki" else swarm_instructions()).encode()).hexdigest()


def load_completed(results_path: Path, cohort: dict) -> dict:
    """Read validated results keyed by canonical record ID. A torn final line (crash mid-write)
    is ignored so that ID is resubmitted; any other invalid row, duplicate ID, ID outside the
    frozen cohort, or changed episode/turn assignment is an error."""
    expected = {e["id"]: e for e in cohort["records"]}
    done: dict = {}
    if not results_path.exists():
        return done
    lines = results_path.read_text(encoding="utf-8").split("\n")
    for n, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            ann = TraceAnnotation.model_validate_json(line)
        except Exception:
            if all(not x.strip() for x in lines[n + 1 :]):
                continue  # torn trailing write
            raise RuntimeError(f"{results_path}:{n + 1} is not a valid TraceAnnotation")
        rid = ann.record_id
        if rid not in expected:
            raise RuntimeError(f"{results_path}:{n + 1} has ID {rid} outside the frozen cohort")
        if rid in done:
            raise RuntimeError(f"{results_path}:{n + 1} duplicates {rid}")
        e = expected[rid]
        if ann.episode_id != e["episode_id"] or ann.turn_index != e["turn_index"]:
            raise RuntimeError(f"{rid}: stored episode/turn differs from the frozen cohort")
        done[rid] = ann
    return done


def repair_torn_tail(path: Path) -> int:
    """Drop an unterminated final line left by a crash mid-write so later appends start on a
    fresh line. Every complete write ends with a newline, so a missing one means a torn write.
    Returns the number of bytes removed."""
    if not path.exists():
        return 0
    data = path.read_bytes()
    if not data or data.endswith(b"\n"):
        return 0
    keep = data.rfind(b"\n") + 1
    with open(path, "r+b") as f:
        f.truncate(keep)
        f.flush()
        os.fsync(f.fileno())
    return len(data) - keep


def append_durable(path: Path, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_rows_by_id(input_path: Path, ids: set) -> dict:
    rows: dict = {}
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if len(rows) == len(ids):
                break
            m = re.match(r'\{"id":\s*"([^"]+)"', line[:40])  # cheap prefilter before json parse
            if m and m.group(1) in ids:
                rows[m.group(1)] = json.loads(line)
    missing = ids - rows.keys()
    if missing:
        raise RuntimeError(f"cohort IDs not found in corpus: {sorted(missing)[:5]}")
    return rows


async def run_resumable(args: argparse.Namespace, classify=None) -> int:
    """0: every cohort ID has a validated row. 2: some IDs still missing (rerun to retry).
    3: stopped early by --stop-after."""
    import socket
    import time

    source = getattr(args, "source", "swarm")
    if source == "wiki":
        configure_wiki(getattr(args, "wiki_prompt", None), getattr(args, "abstain", False))
    else:
        configure_swarm(getattr(args, "swarm_prompt", None), getattr(args, "abstain", False))
    classify = classify or (classify_wiki_record if source == "wiki" else classify_record)
    pilot = Path(args.pilot_dir)
    pilot.mkdir(parents=True, exist_ok=True)
    cohort_path, results_path = pilot / "cohort.json", pilot / "results.jsonl"
    fail_path, log_path = pilot / "failures.jsonl", pilot / "run_log.jsonl"

    ensure_api_key()
    input_path = resolve_input_path(args.input)
    cohort = freeze_cohort(cohort_path, input_path, args)
    entries = cohort["records"]
    torn_bytes = repair_torn_tail(results_path)
    if torn_bytes:
        append_durable(log_path, json.dumps({"event": "repaired_torn_tail", "bytes": torn_bytes}))
        print(f"[!] removed {torn_bytes} bytes of torn trailing write from {results_path.name}")
    done = load_completed(results_path, cohort)
    todo = [e for e in entries if e["id"] not in done]
    if not todo:
        rows = {}
    elif source == "wiki":
        allrows = load_wiki_records(input_path)
        rows = {e["id"]: allrows[e["id"]] for e in todo}
    else:
        rows = load_rows_by_id(input_path, {e["id"] for e in todo})

    append_durable(log_path, json.dumps({
        "event": "run_start", "host": socket.gethostname(), "model": args.model,
        "concurrency": args.concurrency, "cohort_size": len(entries),
        "already_completed": len(done), "skipped_completed": sorted(done),
        "submitting": [e["id"] for e in todo], "ts": time.time(),
    }))
    print(
        f"[*] pilot cohort {len(entries)} | already done {len(done)} (skipped) | "
        f"submitting {len(todo)} | concurrency {args.concurrency}"
    )

    sem = asyncio.Semaphore(args.concurrency)
    # The SDK default read timeout is 60 s. Some Swarm Traces fragments make the model reason
    # longer than that, which fails the same records on every retry. A timeout does not change labels.
    client = AsyncAdaption(timeout=float(getattr(args, "timeout", 300.0))) if todo else None
    t0 = time.monotonic()
    written = failed = 0

    async def one(e: dict):
        t_start = time.monotonic()
        try:
            ann = await classify(sem, client, rows[e["id"]], e["turn_index"], args.model)
            ann.episode_id = e["episode_id"]  # keep the frozen assignment
            ann.turn_index = e["turn_index"]
            return e, ann, None, time.monotonic() - t_start
        except Exception as exc:  # noqa: BLE001
            return e, None, exc, time.monotonic() - t_start

    tasks = [asyncio.create_task(one(e)) for e in todo]
    try:
        for fut in asyncio.as_completed(tasks):
            e, ann, exc, latency = await fut
            if ann is not None:
                append_durable(results_path, ann.model_dump_json())
                append_durable(log_path, json.dumps({
                    "event": "result", "id": e["id"], "latency_s": round(latency, 3),
                    "t_s": round(time.monotonic() - t0, 3)}))
                written += 1
            else:
                append_durable(fail_path, json.dumps({
                    "id": e["id"], "error": str(exc)[:500], "ts": time.time()}))
                failed += 1
            if args.stop_after and written >= args.stop_after:
                append_durable(log_path, json.dumps({"event": "stopped_early", "written": written}))
                print(f"[!] --stop-after {args.stop_after} reached; stopping")
                return 3
    finally:
        for t in tasks:
            t.cancel()

    elapsed = time.monotonic() - t0
    done = load_completed(results_path, cohort)
    missing = [e["id"] for e in entries if e["id"] not in done]
    append_durable(log_path, json.dumps({
        "event": "run_end", "written": written, "failed": failed, "missing": missing,
        "elapsed_s": round(elapsed, 3),
        "records_per_min": round(written / elapsed * 60, 2) if elapsed and written else 0.0,
    }))
    print(f"[+] wrote {written}, failed {failed}, missing {len(missing)}, {elapsed:.1f}s")
    if missing:
        print(f"[!] {len(missing)} IDs still missing; rerun the same command to retry them")
        return 2

    ordered = [done[e["id"]] for e in entries]
    with open(pilot / "final.jsonl", "w", encoding="utf-8") as f:
        for ann in ordered:
            f.write(ann.model_dump_json() + "\n")
    (pilot / "summary.json").write_text(
        json.dumps(compute_markov_analytics(ordered), indent=2), encoding="utf-8")
    print(f"[+] complete: {pilot / 'final.jsonl'} ({len(ordered)} rows)")
    return 0


async def run_batch(args: argparse.Namespace) -> None:
    ensure_api_key()
    input_path = resolve_input_path(args.input)
    out_dir = Path(__file__).resolve().parent
    output_jsonl = Path(args.output) if args.output else out_dir / "vsm_batch_output.jsonl"
    summary_json = out_dir / "vsm_markov_summary.json"

    if args.mode == "stratified":
        cohort = select_stratified_cohort(
            input_path,
            payload_sample=args.payload_sample,
            dag_children_per_tree=args.dag_children,
        )
    else:
        cohort = []
        with open(input_path, "r", encoding="utf-8") as f:
            for i in range(args.limit):
                line = f.readline()
                if not line:
                    break
                cohort.append(json.loads(line))

    if args.limit and len(cohort) > args.limit:
        cohort = cohort[: args.limit]

    print(
        f"[*] Dispatching {len(cohort)} records (mode={args.mode}, concurrency={args.concurrency}, "
        f"model={args.model})..."
    )

    # Assign sequential turn_index within each episode
    episode_turn_counters: Counter = Counter()
    tasks_spec: list[tuple[dict, int]] = []
    for row in cohort:
        meta = extract_forensic_metadata(row)
        ep_id = row.get("_episode_override") or meta["episode_id"]
        t_idx = episode_turn_counters[ep_id]
        episode_turn_counters[ep_id] += 1
        tasks_spec.append((row, t_idx))

    sem = asyncio.Semaphore(args.concurrency)
    client = AsyncAdaption()

    coros = [
        classify_record(sem, client, row, t_idx, args.model)
        for row, t_idx in tasks_spec
    ]
    annotations = await asyncio.gather(*coros)

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for ann in annotations:
            f.write(ann.model_dump_json() + "\n")

    analytics = compute_markov_analytics(annotations)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(analytics, f, indent=2)

    print_summary(annotations, analytics)
    print(f"\n[+] Saved {len(annotations)} annotated records to {output_jsonl}")
    print(f"[+] Saved Markov transition analytics to {summary_json}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch VSM Cybernetic Classifier & Markov Transition Analyzer"
    )
    parser.add_argument("--input", type=str, default=None, help="Path to redacted.jsonl")
    parser.add_argument("--output", type=str, default=None, help="Path to output JSONL")
    parser.add_argument(
        "--mode",
        choices=["stratified", "head"],
        default="stratified",
        help="'stratified' (payload stream + DAG trees + all 37 tagged forensic commands) or 'head' (first N rows)",
    )
    parser.add_argument(
        "--payload-sample",
        type=int,
        default=10,
        help="Number of initial sequential payload records in stratified mode",
    )
    parser.add_argument(
        "--dag-children",
        type=int,
        default=2,
        help="Number of child records per parent root in stratified mode",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=60,
        help="Maximum total records to classify in this batch run",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Async worker concurrency for Adaption API calls",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3.5-397b",
        help="Adaption model identifier",
    )
    parser.add_argument(
        "--pilot-dir", type=str, default=None,
        help="Resumable mode: freeze the cohort and keep per-ID results in this directory, "
        "separate from the legacy vsm_batch_output.jsonl. Rerun the same command to resume.",
    )
    parser.add_argument(
        "--episodes", type=str, default=None,
        help="Comma-separated episode IDs for the pilot cohort (default: six bounded episodes)",
    )
    parser.add_argument("--stop-after", type=int, default=0, help="Test hook: stop after N new results")
    parser.add_argument("--timeout", type=float, default=300.0,
                        help="Pilot mode: per-request timeout in seconds (SDK default is 60)")
    parser.add_argument(
        "--source", choices=["swarm", "wiki"], default="swarm",
        help="Pilot mode corpus: 'swarm' (redacted.jsonl) or 'wiki' (records.jsonl.gz, pass --input)",
    )
    parser.add_argument("--wiki-min-per-page", type=int, default=2, help="Wiki: min dated records per page")
    parser.add_argument("--wiki-cap", type=int, default=50, help="Wiki: max records per page (earliest first)")
    parser.add_argument("--wiki-pages", type=int, default=0, help="Wiki: deterministic page subset (0 = all)")
    parser.add_argument("--wiki-prompt", type=str, default=None,
                        help="Wiki: prompt file (default calibration/wiki_prompt.md)")
    parser.add_argument("--abstain", action="store_true",
                        help="Wiki: require evidence_status (sufficient / insufficient_evidence) in every answer")
    parser.add_argument("--swarm-cohort", choices=["legacy", "stratified"], default="legacy",
                        help="Swarm pilot cohort: 'legacy' (stratified episodes) or 'stratified' random by kind")
    parser.add_argument("--swarm-n", type=int, default=6000, help="Swarm stratified sample size")
    parser.add_argument("--seed", type=int, default=0, help="Sampling seed")
    parser.add_argument("--swarm-prompt", type=str, default=None,
                        help="Swarm: prompt file (default: original INSTRUCTIONS)")
    parser.add_argument("--cohort-from", type=str, default=None,
                        help="Freeze a new pilot dir with exactly this cohort.json's IDs, episodes and turns")
    args = parser.parse_args()
    if args.pilot_dir:
        raise SystemExit(asyncio.run(run_resumable(args)))
    asyncio.run(run_batch(args))


if __name__ == "__main__":
    main()

