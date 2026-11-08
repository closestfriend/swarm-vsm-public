from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class VSMSystem(str, Enum):
    S0_NOISE = "S0_NOISE"
    S1_OPERATIONS = "S1_OPERATIONS"  # direct atomic tool/task execution
    S2_COORDINATION = "S2_COORDINATION"  # anti-oscillation, shared filesystem boards, lockfiles, status ledgers
    S3_CONTROL = "S3_CONTROL"  # vertical task allocation, splitting goals into sub-tasks, delegation
    S3_STAR_AUDIT = "S3_STAR_AUDIT"  # sporadic unmediated verification, checksums, diffs, abort triggers
    S4_INTELLIGENCE = "S4_INTELLIGENCE"  # environmental recon, boundary/filter probing
    S5_POLICY = "S5_POLICY"  # global doctrine, stealth posture, alias/lineage closure


class CadenceMode(str, Enum):
    SYNCHRONOUS_FAST = "SYNCHRONOUS_FAST"
    ASYNCHRONOUS_SLOW = "ASYNCHRONOUS_SLOW"
    BROADCAST_STATE = "BROADCAST_STATE"


class VarietyOperator(str, Enum):
    AMPLIFIER = "AMPLIFIER"
    ATTENUATOR = "ATTENUATOR"


class RecordKind(str, Enum):
    PAYLOAD = "payload"
    RESPONSE = "response"
    RECOVERED_TEXT = "recovered_text"


class TraceAnnotation(BaseModel):
    # Core VSM fields
    trace_id: str = Field(description="Record ID (e.g. R0000001) or trajectory episode ID")
    turn_index: int = Field(description="0-indexed sequential turn within the trajectory/episode")
    source_agent_id: str = Field(description="Agent/runtime/credential identifier initiating the turn")
    target_agent_ids: list[str] = Field(
        default_factory=list,
        description="Addressed endpoints, services, shared boards, or downstream agents",
    )
    reasoning_chain: str = Field(
        description="1-2 sentences analyzing operational mechanics, cybernetic role, and variety flow"
    )
    primary_vsm: VSMSystem
    secondary_vsm: Optional[VSMSystem] = None
    cadence_mode: CadenceMode
    variety_operator: VarietyOperator
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_status: Optional[Literal["sufficient", "insufficient_evidence"]] = Field(
        default=None,
        description=(
            "Whether the record's text can support a VSM label. When insufficient_evidence, "
            "primary_vsm is the judge's best guess only and should be excluded from label counts. "
            "None means the run did not ask (all runs before the abstention option)."
        ),
    )

    # Extended forensic & temporal topology metadata (populated from corpus or model)
    record_id: Optional[str] = Field(
        default=None, description="Canonical corpus ID (e.g. R0189543)"
    )
    parent_id: Optional[str] = Field(
        default=None, description="Causal parent record ID in the DAG, if any"
    )
    episode_id: Optional[str] = Field(
        default=None,
        description="Logical trajectory/episode grouping (e.g. g23619cmd.bin, parent root ID, or session)",
    )
    record_kind: Optional[RecordKind] = Field(
        default=None, description="Corpus record kind: payload, response, or recovered_text"
    )
    tags: Optional[str] = Field(
        default=None, description="Forensic tags (e.g. article-evidence;g236-command;...)"
    )
    embedded_timestamp: Optional[str] = Field(
        default=None,
        description="Extracted embedded timestamp or sequence marker from payload/metadata if present",
    )
    shared_artifacts: list[str] = Field(
        default_factory=list,
        description="Referenced shared filesystem boards, lockfiles, token ledgers, or repos (e.g. /tmp/g236_tokens.json)",
    )
