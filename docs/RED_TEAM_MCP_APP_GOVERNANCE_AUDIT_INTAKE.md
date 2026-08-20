# Bounded audit intake checklist

This checklist is a public orientation aid, not a data-submission channel.
Share any information only through a separately approved route after the scope
and data boundary have been accepted by the responsible people.

## Confirm the audit unit

- Name one MCP server or ChatGPT app.
- Define one reviewable audit run and the decision it should inform.
- Name the person accountable for accepting, revising or stopping the result.

## Prepare only allowed evidence

- Include bounded tool metadata and declared permission or host boundaries.
- Include only an agreed injection-control profile and limited, cleared test or
  release evidence.
- State what runtime evidence is observed, verified or not tested.

## Exclude sensitive material

- Do not include credentials, tokens, passwords, private keys or MFA material.
- Do not include payment data, raw customer records, unrestricted logs or
  unapproved personal data.
- Do not request network scans, live exploitation, code execution, automatic
  repair or automatic publication.

## Define the decision boundary

Before work starts, agree the scope, the acceptable data classes, the evidence
required for a `GREEN` result and the human decision that follows the report.
Any material change requires a newly bounded review or re-audit.
