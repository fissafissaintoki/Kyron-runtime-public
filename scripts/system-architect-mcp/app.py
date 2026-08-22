from __future__ import annotations

import os
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field
from starlette.requests import Request
from starlette.responses import JSONResponse


SERVER_INSTRUCTIONS = (
    "KYRON System Architect is a bounded, read-only architecture assistant. "
    "It returns structured guidance from user-supplied inputs only. "
    "It does not access credentials, local files, private KYRON infrastructure, "
    "external providers, or mutable external state. The human remains owner."
    " Do not provide credentials, secrets, personal data, or customer records."
)


class _OutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArchitectSystemResult(_OutputModel):
    process_name: str
    objective: str
    owner: Literal["HUMAN_OWNER"]
    mode: Literal["AUDIT_THEN_BUILD"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    constraints: list[str]
    boundaries: list[str]
    gates: list[str]
    evidence_required: list[str]
    safe_next_step: str


class DiagnoseSystemResult(_OutputModel):
    process_name: str
    status: Literal["MATCH", "GAP"]
    observed_state: str
    expected_state: str
    evidence_count: int
    problem_class: Literal["NONE", "STATE_MISMATCH"]
    missing_evidence: list[str]
    safe_next_step: str


class MCPWorkflowStep(_OutputModel):
    step: int
    action: str
    gate: str


class MCPWorkflowPlanResult(_OutputModel):
    goal: str
    declared_tools: list[str]
    execution: Literal["NOT_EXECUTED"]
    steps: list[MCPWorkflowStep]
    write_status: Literal["OWNER_APPROVAL_REQUIRED", "NO_WRITES_REQUESTED"]


class ProductionManifestResult(_OutputModel):
    service_name: str
    public_mcp_url: str
    auth_mode: Literal["NONE", "OAUTH"]
    external_domains: list[str]
    checks: list[str]
    status: Literal["READY_FOR_EXTERNAL_VERIFICATION", "BLOCKED"]
    blockers: list[str]


class EvidenceReceiptResult(_OutputModel):
    receipt_id: str
    status: Literal["DECLARED_FIELDS_PASS", "DECLARED_FIELDS_BLOCKED"]
    verification_scope: Literal["DECLARED_FIELDS_ONLY"]
    blockers: list[str]


def _annotations() -> ToolAnnotations:
    return ToolAnnotations(
        read_only_hint=True,
        open_world_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
    )


def _hosts() -> list[str]:
    hosts = ["testserver"]
    for key in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
        value = os.getenv(key, "").strip()
        if value:
            hosts.append(value)
    return sorted(set(hosts))


mcp = MCPServer(
    "KYRON System Architect",
    version="1.1.0",
    instructions=SERVER_INSTRUCTIONS,
)


@mcp.tool(
    title="Architect a governed system",
    description="Turn a process objective into a bounded architecture with ownership, controls, gates, evidence, and a safe next step.",
    annotations=_annotations(),
    structured_output=True,
)
def architect_system(
    process_name: Annotated[str, Field(min_length=1, max_length=160)],
    objective: Annotated[str, Field(min_length=1, max_length=4000)],
    constraints: Annotated[list[str], Field(max_length=20)] = [],
    risk_level: Annotated[str, Field(pattern="^(LOW|MEDIUM|HIGH)$")] = "MEDIUM",
) -> ArchitectSystemResult:
    gates = ["OWNER_GATE", "EVIDENCE_GATE", "QUALITY_GATE"]
    if risk_level == "HIGH":
        gates.insert(1, "RED_TEAM_GATE")
    return {
        "process_name": process_name,
        "objective": objective,
        "owner": "HUMAN_OWNER",
        "mode": "AUDIT_THEN_BUILD",
        "risk_level": risk_level,
        "constraints": constraints,
        "boundaries": [
            "No credential access",
            "No local filesystem access",
            "No external writes",
            "No provider execution",
        ],
        "gates": gates,
        "evidence_required": [
            "Declared inputs",
            "Decision rationale",
            "Verification result",
            "Owner approval for consequential actions",
        ],
        "safe_next_step": "Validate the proposed architecture against the real process before implementation.",
    }


@mcp.tool(
    title="Diagnose a governed system",
    description="Compare user-supplied observed and expected process states and identify a deterministic mismatch class and next check. It does not independently verify evidence.",
    annotations=_annotations(),
    structured_output=True,
)
def diagnose_system(
    process_name: Annotated[str, Field(min_length=1, max_length=160)],
    observed_state: Annotated[str, Field(min_length=1, max_length=4000)],
    expected_state: Annotated[str, Field(min_length=1, max_length=4000)],
    evidence: Annotated[list[str], Field(max_length=30)] = [],
) -> DiagnoseSystemResult:
    status = "MATCH" if observed_state.strip() == expected_state.strip() else "GAP"
    return {
        "process_name": process_name,
        "status": status,
        "observed_state": observed_state,
        "expected_state": expected_state,
        "evidence_count": len(evidence),
        "problem_class": "NONE" if status == "MATCH" else "STATE_MISMATCH",
        "missing_evidence": [] if evidence else ["Independent evidence supporting the observed state"],
        "safe_next_step": "Verify the mismatch with independent evidence before changing the process.",
    }


@mcp.tool(
    title="Plan a bounded MCP workflow",
    description="Convert a goal and declared tool set into a gated workflow without invoking any tool.",
    annotations=_annotations(),
    structured_output=True,
)
def plan_mcp_workflow(
    goal: Annotated[str, Field(min_length=1, max_length=4000)],
    available_tools: Annotated[list[str], Field(min_length=1, max_length=20)],
    write_actions_requested: bool = False,
) -> MCPWorkflowPlanResult:
    return {
        "goal": goal,
        "declared_tools": available_tools,
        "execution": "NOT_EXECUTED",
        "steps": [
            {"step": 1, "action": "Validate inputs and scope", "gate": "INPUT_GATE"},
            {"step": 2, "action": "Select only declared tools", "gate": "TOOL_BOUNDARY"},
            {"step": 3, "action": "Collect evidence", "gate": "EVIDENCE_GATE"},
            {
                "step": 4,
                "action": "Request human approval before consequential writes"
                if write_actions_requested
                else "Return read-only result",
                "gate": "OWNER_GATE" if write_actions_requested else "QUALITY_GATE",
            },
        ],
        "write_status": "OWNER_APPROVAL_REQUIRED" if write_actions_requested else "NO_WRITES_REQUESTED",
    }


@mcp.tool(
    title="Build a production manifest",
    description="Evaluate supplied public MCP deployment metadata and return a readiness manifest without contacting the endpoint.",
    annotations=_annotations(),
    structured_output=True,
)
def build_production_manifest(
    service_name: Annotated[str, Field(min_length=1, max_length=160)],
    public_mcp_url: Annotated[str, Field(min_length=1, max_length=500)],
    auth_mode: Annotated[str, Field(pattern="^(NONE|OAUTH)$")] = "NONE",
    external_domains: Annotated[list[str], Field(max_length=20)] = [],
) -> ProductionManifestResult:
    blockers = []
    if not public_mcp_url.startswith("https://"):
        blockers.append("Public MCP URL must use HTTPS.")
    if external_domains and auth_mode != "OAUTH":
        blockers.append("External app connections require user-scoped OAuth.")
    return {
        "service_name": service_name,
        "public_mcp_url": public_mcp_url,
        "auth_mode": auth_mode,
        "external_domains": external_domains,
        "checks": [
            "TLS endpoint declared",
            "Streamable HTTP MCP path declared",
            "No shared publisher credentials",
            "Secret redaction required",
            "External initialize/tools-list verification required",
        ],
        "status": "READY_FOR_EXTERNAL_VERIFICATION" if not blockers else "BLOCKED",
        "blockers": blockers,
    }


@mcp.tool(
    title="Validate declared evidence receipt fields",
    description="Validate user-supplied receipt fields deterministically. It does not hash an artifact or reach an endpoint.",
    annotations=_annotations(),
    structured_output=True,
)
def verify_evidence_receipt(
    receipt_id: Annotated[str, Field(min_length=1, max_length=180)],
    artifact_sha256: Annotated[str, Field(min_length=64, max_length=64)],
    quality_gate_status: Annotated[str, Field(pattern="^(GREEN|RED)$")],
    endpoint_status: Annotated[str, Field(pattern="^(REACHABLE|UNREACHABLE)$")],
    owner_approval: bool,
) -> EvidenceReceiptResult:
    blockers = []
    if len(artifact_sha256) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in artifact_sha256):
        blockers.append("Artifact SHA-256 is invalid.")
    if quality_gate_status != "GREEN":
        blockers.append("Quality gate is not GREEN.")
    if endpoint_status != "REACHABLE":
        blockers.append("Endpoint is not REACHABLE.")
    if not owner_approval:
        blockers.append("Human owner approval is missing.")
    return {
        "receipt_id": receipt_id,
        "status": "DECLARED_FIELDS_PASS" if not blockers else "DECLARED_FIELDS_BLOCKED",
        "verification_scope": "DECLARED_FIELDS_ONLY",
        "blockers": blockers,
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "KYRON System Architect",
            "version": mcp.version,
            "mcp_endpoint": "/mcp",
            "public_runtime": True,
        }
    )


app = mcp.streamable_http_app(
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        allowed_hosts=_hosts(),
        allowed_origins=[],
    ),
)
