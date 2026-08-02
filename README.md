# KYRON — Public Release Channel

This repository is KYRON's controlled public presentation and release layer.
It shows approved outcomes and verification evidence without exposing the
private implementation, knowledge base or operating environment.

## Current status

**PUBLIC CHANNEL READY — no downloadable production release is currently
approved.**

When a release is added, it is official only if its manifest passes the Public
Release Gate and every published file matches the recorded SHA-256 digest.

## What may appear here

- concise product and outcome descriptions;
- selected, metadata-cleaned screenshots;
- user documentation and changelogs;
- rights, security and third-party notices;
- approved release payloads, manifests and checksums.

## What will not appear here

- private source code or internal architecture;
- prompts, raw dialogues, memory or knowledge records;
- credentials, runtime data, local paths or operating evidence;
- internal tests, decision logic or deployment access.

## Trust model

The official state is controlled by the repository owner. Outside users cannot
change it without repository permission. Forks, copies and modified uploads are
not part of the canonical KYRON release channel.

Public files can nevertheless be downloaded and copied. Public visibility is
not an open-source license. See [RIGHTS.md](RIGHTS.md) and
[docs/TRUST_MODEL.md](docs/TRUST_MODEL.md).

## Verification

Repository safety is checked on every pull request. Approved release payloads
are verified with:

```bash
python scripts/verify_release.py \
  --manifest releases/<release>/release-manifest.json \
  --artifact-dir releases/<release>/payload
```

Security reports: [SECURITY.md](SECURITY.md)  
Release history: [CHANGELOG.md](CHANGELOG.md)  
Third-party rights: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
