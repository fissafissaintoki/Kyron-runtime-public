# KYRON — Public Release Channel

This repository is KYRON's controlled public presentation and release layer.
It shows approved outcomes and verification evidence without exposing the
private implementation, knowledge base or operating environment.

## Current status

**PUBLIC APPROVED — KYRON DJ Operator v0.1.**

Public application:

**https://fissafissaintoki.github.io/Kyron-runtime-public/**

The DJ Operator is a free, installable, local-first two-deck audio application.
Audio files remain on the user's device. The published release contains no
credentials, external provider dependency or uploaded audio.

The release is official only when its generated manifest passes the Public
Release Gate and every published file matches the recorded SHA-256 digest.
The deployed site also exposes `release-manifest.json` for verification.

## Approved capabilities

- two local audio decks with play, seek and gain;
- equal-power crossfader;
- local waveform generation;
- BPM tap, manual BPM and bounded deck synchronization;
- four cue points per deck;
- local low, mid and high energy analysis with Teacher View guidance;
- set list, session notes and metadata-only JSON import/export;
- installable desktop, iOS and Android PWA shell.

## What may appear here

- concise product and outcome descriptions;
- selected, metadata-cleaned screenshots;
- user documentation and changelogs;
- rights, security and third-party notices;
- approved release payloads, manifests and checksums.

## What will not appear here

- private source code or internal architecture;
- prompts, raw dialogues, memory or knowledge records;
- credentials, operating data, local paths or internal evidence;
- internal tests, decision logic or deployment access;
- user audio files or session content.

## Trust model

The official state is controlled by the repository owner. Outside users cannot
change it without repository permission. Forks, copies and modified uploads are
not part of the canonical KYRON release channel.

Public files can nevertheless be downloaded and copied. Public visibility is
not an open-source license. See [RIGHTS.md](RIGHTS.md) and
[docs/TRUST_MODEL.md](docs/TRUST_MODEL.md).

## Verification

Repository safety is checked on every pull request. The DJ Operator manifest is
generated deterministically from the payload and verified before deployment.

Security reports: [SECURITY.md](SECURITY.md)  
Release history: [CHANGELOG.md](CHANGELOG.md)  
Third-party rights: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
