# KYRON — Governed AI Operator Runtime

KYRON is a controlled runtime for turning recurring operational work into bounded, reviewable AI-assisted workflows.

Organizations already have access to powerful models. The harder problem is making AI work **repeatable, measurable and governable** without handing final authority to an opaque system.

KYRON is built around that problem.

## Start here — KYRON Agent Assurance

**[KYRON Agent Assurance](https://kyron-agent-assurance.faekalius345328.chatgpt.site)** is the public commercial entry point for teams preparing an MCP server or AI agent for a bounded release.

It produces a versioned, reviewable assurance pack from an agreed scope: the declared tool surface, permission and action boundaries, supplied control evidence, open findings and a receipt. It assesses supplied metadata and evidence; it does not access customer systems, execute tests in production or certify regulatory compliance.

The initial engagement is deliberately narrow: one named agent or MCP surface, one agreed review run and clear release/rework evidence.

## Live developer surface

The read-only **KYRON System Architect** runtime is available at [MCP endpoint](https://kyron-runtime-public.vercel.app/mcp); its [health check](https://kyron-runtime-public.vercel.app/health) reports the deployed service and version. It provides deterministic planning and metadata checks from user-supplied inputs only.

## Why a team would use KYRON

KYRON is intended for workflows where:

- experts repeatedly spend time turning messy inputs into a defined work product;
- inconsistent outputs create rework, delay or escalation;
- a human must remain accountable for the result;
- the organization needs evidence that the AI workflow behaved inside its approved boundary;
- private operating logic must remain protected.

The product is not "chat with another AI." The product is a configured, governed work capability with a measurable acceptance contract.

## Commercial workflow pilots

The first commercial engagement is deliberately narrow: **one workflow, one bounded scope, measurable before/after evidence.**

A pilot can include:

- current-process baseline;
- input/output definition;
- human approval boundary;
- representative evaluation cases;
- controlled KYRON candidate;
- operational scorecard;
- go/revise/stop recommendation for production deployment.

See [Commercial Workflow Pilot](docs/COMMERCIAL_PILOT.md).

## What creates value

A successful KYRON workflow should improve an operational measure the buyer already cares about, such as:

- cycle time;
- expert touch time;
- completeness and consistency;
- avoidable rework;
- escalation load;
- trace/evidence coverage;
- policy adherence.

Claims are evaluated against a baseline. A polished demo is not treated as proof by itself.

## Control model

KYRON is designed around explicit boundaries:

- scoped capability instead of unlimited autonomy;
- approved access instead of implicit reach;
- blocked unsafe/out-of-scope actions instead of improvisation;
- human ownership where final accountability is required;
- verification evidence for approved releases and evaluations;
- controlled upgrades instead of uncontrolled self-modification.

Private implementation, internal prompts, knowledge structures and Operator IP are not part of this public release channel.

## Public reference release — KYRON DJ Operator v0.1

**PUBLIC APPROVED.**

The current public reference release is the KYRON DJ Operator, a free, installable, local-first two-deck audio application. It is a reference release, not the commercial entry point.

It demonstrates the release-channel principles in a bounded domain: local data handling, explicit capabilities, deterministic release manifests and public verification evidence.

Approved capabilities include:

- two local audio decks with play, seek and gain;
- equal-power crossfader;
- local waveform generation;
- BPM tap, manual BPM and bounded deck synchronization;
- four cue points per deck;
- local low, mid and high energy analysis with Teacher View guidance;
- set list, session notes and metadata-only JSON import/export;
- installable desktop, iOS and Android PWA shell.

The DJ Operator demonstrates bounded release-channel principles in a low-risk domain. It is not the boundary of KYRON's commercial operational use.

## Public release boundary

This repository is KYRON's controlled public presentation and release layer. It shows approved outcomes and verification evidence without exposing the private implementation, knowledge base or operating environment.

### May appear here

- concise product and outcome descriptions;
- synthetic or approved sanitized examples;
- selected, metadata-cleaned screenshots;
- user documentation and changelogs;
- high-level trust and governance descriptions;
- rights, security and third-party notices;
- approved release payloads, manifests and checksums.

### Will not appear here

- private source code or internal architecture details;
- system prompts, raw dialogues, memory or knowledge records;
- credentials, operating data, local paths or internal evidence;
- proprietary routing, scoring or decision logic;
- private tests or deployment access;
- customer data that is not explicitly cleared for publication.

## Trust model

The official state is controlled by the repository owner. Outside users cannot change it without repository permission. Forks, copies and modified uploads are not part of the canonical KYRON release channel.

Public files can nevertheless be downloaded and copied. Public visibility is not an open-source license. See [RIGHTS.md](RIGHTS.md) and [docs/TRUST_MODEL.md](docs/TRUST_MODEL.md).

## Verification

Repository safety is checked on every pull request. Approved release payloads are verified against their generated manifests before deployment.

Security reports: [SECURITY.md](SECURITY.md)  
Release history: [CHANGELOG.md](CHANGELOG.md)  
Third-party rights: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
