# Independent review of shared guidance proposals

Reviewed the three proposed guidance files and guidance-proposal-review.md against
config/global.agents.md, root AGENTS.md, the canonical playbook, and the references
to which the proposal moves detail. This was a read-only semantic review; no live
guidance was applied and no runtime tests were run.

Status: all four findings below were incorporated into the final drafts. The
findings preserve the review-time wording; line labels refer to that draft
snapshot. Current resolution is recorded in `guidance-proposal-review.md`.

The proposals preserve the important Dobby/control-plane boundaries: person data
versus shared implementation, canonical versus generated sources, identity-client
scope, plugin versus standalone capability ownership, secret-free media flags,
documented automation, and evidence-backed completion. Referenced source files and
the displayed bootstrap/check --repo options exist. I found no security-critical
loss or broken proposed route.

Four small contract changes deserve resolution before activation. They do not
require restoring the old instruction volume.

## 1. Preserve the explicit tracker closeout gate

- Original: [global guidance:33](/Users/dobby/GitHub/agents/config/global.agents.md)
  requires archiving a completed tracker before final handoff, or explicitly
  stating the blocker.
- Proposed: [global:19](proposed-global.agents.md)
  says completed trackers belong in the archive; the
  [playbook:43](proposed-agent-native-repo-playbook.md)
  says to archive according to repo contract, without the final-handoff gate.

The direction is retained, but the operational completion condition is weaker.
Completed active trackers were one of the user's stated concerns; a cold agent
could read this as eventual maintenance. Preserve the short condition: archive
completed trackers before final handoff, or name the concrete blocker.
This does not authorize archiving a project whose acceptance remains unproven,
such as the current home-automation hardware work.

## 2. Acknowledge or narrow the compatibility exception

- Original: [global:23](/Users/dobby/GitHub/agents/config/global.agents.md)
  permits compatibility when the user explicitly asks or repo guidance requires it.
- Proposed: [global:22](proposed-global.agents.md)
  additionally permits it when existing consumer contracts require it.
- The preservation table currently calls the clean migration default retained at
  [review:30](guidance-proposal-review.md).

This can be a sensible deliberate policy choice, but is not exact preservation.
If a consumer's mere existence is treated as a compatibility requirement, agents
may add dual reads, legacy schema paths or shims instead of completing an
authorized cross-repo migration. Either retain the original exception, or say
documented consumer compatibility requirements and make clear that a clean,
authorized coordinated migration remains preferred. Record the intentional
change in the preservation review if retained.

## 3. Preserve a bounded generated-runtime troubleshooting exception if intended

- Original: [global:22](/Users/dobby/GitHub/agents/config/global.agents.md)
  prohibits hand-editing generated surfaces unless troubleshooting.
- Proposed: [global:26](proposed-global.agents.md)
  makes the prohibition unconditional, as does the compressed root boundary.

Canonical ownership is correctly retained. The specific troubleshooting exception
has nevertheless narrowed: a reversible one-off runtime experiment could now
appear forbidden even during authorized diagnosis. If that capability is still
wanted, retain it narrowly: temporary diagnosis may touch a generated surface,
but durable changes go to its canonical source and final state is restored or
reconciled. If deliberately removed, label this as a stricter policy in the
proposal review rather than unchanged preservation. No broad runtime-edit
permission is recommended.

## 4. Keep the commit-gate authoring contract discoverable

- Original: [global:52](/Users/dobby/GitHub/agents/config/global.agents.md)
  requires fast checks to be deterministic, local, quick and actionable;
  [root:95](/Users/dobby/GitHub/agents/AGENTS.md) favors staged/affected checks
  and reserves broader validation for check-full.
- Proposed: [root:69](proposed-agents-root.md)
  names fast/full entrypoints, but not the authoring constraints.
- The substantive contract still exists in
  [playbook best-practices:77](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/references/best-practices.md)
  and [line 92](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/references/best-practices.md),
  now conditionally routed only for broader operating-model design.

This is not a lost safety rule everywhere, but the root's hook-authoring route
does not make the Git fast-gate constraint clear. Native-hook speed guidance
in the lifecycle reference is not the same contract. Keep a short conditional
rule for editing commit-time checks, or route that exact contract from the
lifecycle/check reference: local deterministic fast gates; affected validation
where appropriate; slower or live checks separate. This protects the unattended
Stop-hook workflow without instructing every typo fix to rerun more tests.

## Existing companion work is correctly identified

The proposal review already requires updating old mandatory principles/docs
references and dashboard token-canon guidance before activation. Keep those as
real prerequisites; merely shortening SKILL.md would leave overprescriptive
instructions available through the conditional routes.

The global nested-guidance instruction is not an unnecessary blanket read:
it correctly compensates for the client's lack of guaranteed dynamic loading.
Repo-specific live-turn, device, secret, parked-service and writer boundaries
remain with their owners. I recommend preserving that arrangement.

Once the four items above are either revised or explicitly recorded as intended
policy choices, the proposal is suitable for a small pilot. No additional global
approval layer, Dobby-specific privacy prose in the global file, mandatory full
suite, or new validation framework is needed.
