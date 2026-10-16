# Agent Execution Strategy: Mac Mini and Hosted Cloud

## Status and Goal

Open; deferred at Adi's request on October 13, 2026. This session is for
documentation and handoff. Resume the evaluation when Adi picks it up again.

Decide where our agent work should run across **Codex and Claude Code**:
our existing Mac Mini and MacBook, each client's hosted cloud environments,
or a combination. Evaluate the workflow we actually use rather than choosing
an execution location around one client's interface.

Adi plans to discuss this with Claude Code before settling the approach.
Neither client is architecturally primary. Claude's review should contribute
to this tracker so the decision remains shared across sessions and clients.

## Starting Point

The initial Codex discussion recommends keeping the Mac Mini as the primary
execution host and adding hosted cloud selectively for contained tasks or
independent investigations. **This is a working hypothesis, not an accepted
architecture decision.** Claude's review and practical evidence may change it.

Our current setup already joins canonical guidance, skills, native client
configuration, MCP assignments, lifecycle hooks, related repositories, and
machine utilities. Development machines own relevant source validation and
product verification; existing repository automation owns delivery.

Distinguish three choices throughout the evaluation:

- **Interface:** where Adi starts, steers, and reviews work.
- **Execution host:** where files, commands, builds, and product checks run.
- **Client/model service:** which agent runtime and provider perform the work.

A convenient remote interface can still target our own machine. Verify the
exact connection's capabilities; an SSH session does not automatically offer
the same browser or desktop access as an interactive Mac session.

## Options and Trade-offs to Evaluate

| Option | Potential benefit | Questions for our workflow |
| --- | --- | --- |
| Mac Mini as primary host | Reuses the prepared environment across clients; persistent state and Mac tooling | Uptime, maintenance, finite compute, stale machine state, and coordination in shared main |
| Native hosted cloud for suitable tasks | Independent execution, reusable environments, and task isolation | Capability discovery, credentials, related repos and services, verification, result integration, limits, and cost for each client |
| Hybrid routing by task | Keeps existing integration while adding independent capacity | Which tasks qualify, who maintains both environments, and whether the extra setup pays for itself |
| Another self-managed remote host, if justified | Could address a measured Mini limitation | Additional maintenance, portability, Mac-specific verification, and actual benefit over the current host |

Cloud task isolation and local shared-main coordination are separate design
choices. Separate workspaces reduce execution collisions but still require
integration of conflicting results. Preserve the existing shared-main contract
unless Adi explicitly chooses to change it.

## Work Remaining

- [ ] Get Claude Code's assessment of this baseline and its own local, remote,
  and hosted execution surfaces. Record agreement, disagreement, and evidence
  here; do not assume Codex capabilities or limits apply to Claude.
- [ ] Inventory the capabilities our real task types require: instructions,
  skills/plugins, MCPs, secrets/authentication, neighboring repos, local services,
  browser/desktop access, Mac tooling, and finalization/delivery hooks.
- [ ] Compare exact execution surfaces for both clients against that inventory.
  Separate supported, configurable, unverified, and unavailable capabilities.
- [ ] Compare operating effort, uptime/recovery, concurrency, state durability,
  isolation, credentials, usage limits, and measured cost/performance where useful.
- [ ] Decide whether practical trials are warranted. If Adi resumes with trial
  authorization, select a representative contained task and an integration-heavy
  task; reproduce the necessary checks and assess the effort and result quality.
- [ ] Record a client-neutral decision, task-routing rules, and any implementation
  plan with ownership, acceptance checks, and recovery steps.

Current authorization is to document the project for later. New environment
provisioning, credential distribution, paid capacity, or workflow migration
needs a resumed scope from Adi.

## Completion Criteria

- A documented decision covers both Codex and Claude Code, including any
  justified differences between their native execution surfaces.
- The recommendation explains which task types run where, with a practical
  account of maintenance and integration costs as well as benefits.
- Required verification and existing delivery contracts remain accounted for.
- Material unknowns are either resolved with evidence or explicitly accepted;
  any implementation work is complete or separately scoped by Adi.

## Evidence and Related Work

- [Control-plane architecture](../../architecture/codex-control-plane.md),
  [capability boundaries](../../architecture/capability-bootstrap-model.md), and
  [runtime ownership](../../references/codex-control-plane-ownership.md).
- [Initial visual comparison](resources/mac-mini-cloud.html), preserved from the
  October 13 Codex discussion. It includes task examples and the provisional
  recommendation. HTML and JavaScript syntax checks passed; interactive browser
  verification was blocked by local-file URL policy.
- Official Codex sources reviewed through the current manual on October 13:
  [Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments)
  and [Remote connections](https://learn.chatgpt.com/docs/remote-connections).
  At that time, the current Cloud guide documented multi-repo environments,
  separate task workspaces, repo-stored skills, and independent execution;
  personal local skills were not synced, and browser/computer use was listed
  as unsupported. Revalidate these product facts when resuming.
- No hosted environment was provisioned, no cross-client trial was run, and
  no pricing or performance advantage has been measured.

## Resume Here

Read this tracker and the linked control-plane architecture and ownership docs,
then add Claude Code's assessment. The first unresolved question is whether
native hosted environments can preserve the capabilities and completion workflow
we need across both clients with enough benefit to justify another environment
to maintain.
