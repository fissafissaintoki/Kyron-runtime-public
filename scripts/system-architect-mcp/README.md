# KYRON System Architect — Public MCP Runtime

This directory is a deliberately minimized public runtime for the KYRON System Architect plugin.

It is not the private KYRON Core. It contains no private runtime modules, prompts, local paths,
provider adapters, credentials, memory, NAS access, or external write capability.

Public endpoints:
- `/health` — health status
- `/mcp` — Streamable HTTP MCP endpoint

The runtime exposes five read-only tools:
- `architect_system`
- `diagnose_system`
- `plan_mcp_workflow`
- `build_production_manifest`
- `verify_evidence_receipt`

Human ownership remains explicit. This runtime does not execute deployments, provider calls,
external writes, or privileged operations.

Use only non-sensitive metadata. Do not submit credentials, secrets, personal data, customer
records, or production payloads. Check `/health` for the deployed version before relying on a
specific release capability.
