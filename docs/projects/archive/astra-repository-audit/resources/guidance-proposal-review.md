# Shared Guidance Proposal Review

These draft files are review artifacts, not live instruction sources:

- `proposed-global.agents.md` → `config/global.agents.md`
- `proposed-agent-native-repo-playbook.md` → `skills-source/owned/agent-native-repo-playbook/SKILL.md`
- `proposed-agents-root.md` → `AGENTS.md`

The draft policy combines autonomous completion with task-dependent context
loading and proportionate evidence. It deliberately avoids assigning a fixed
line budget or model-specific doctrine to every repository. Other models and
clients use the same canonical guidance.

## Contract Preservation

| Existing contract | Draft treatment | Detail remains at |
| --- | --- | --- |
| Human intent; agent implementation through verification and cleanup | Retained explicitly | Global operating model and playbook completion section |
| Existing authorization and material-risk decisions | Retained and clarified | Global operating model; domain-specific repo/skill boundaries |
| Canonical sources versus generated runtime files | Retained; long client-specific list removed from global context | Root source table; control-plane operations and ownership references |
| Skill/plugin registration, native plugin separation, link-first sync | Retained | Root distribution section and registry references |
| MCP target matrix and client rendering rules | Routed conditionally | `mcp/AGENTS.md` and canonical preset schema/renderer |
| Repo/client enablement and identity propagation | Retained | Root distribution section; Codex operations |
| No model/reasoning/profile selection in repo bootstrap registry | Retained | Root distribution section |
| Claude/Copilot/VS Code managed overlays | Source and workflow retained | Existing operations references and canonical overlays |
| Preview checkout substitution and machine-service ownership | Retained | Root distribution section and dev-server registry |
| Exact versioned dashboard production builds | Retained | Dashboard guidance and reference |
| Change-specific sync and regression requirements | Retained as a conditional table | Root Apply and verify section |
| Git automation and no manual commit/push by default | Retained explicitly | Global Files and Git; lifecycle reference for implementation |
| Temporary files, tool session artifacts, clean migration default | Retained, repetition removed | Global Files and Git / Knowledge and guidance |
| Private operational docs and public README distinction | Retained | Global knowledge section; local docs contracts |
| Completed tracker archive | Retained | Global knowledge section and project skill |
| Precise media upload/credential source | Retained | Global Files and Git; media skills for detailed lifecycle |
| Browser fallback | Corrected to available capabilities | Scope decision for dormant agent-browser remains a rollout item |
| Subagent discretion and final ownership | Compressed | Global managed capabilities; project skill for complex delegation |
| Broad playbook discovery and mandatory principles read | Replaced with task-specific references and sufficient evidence | Existing references remain available |

## Required Companion Work Before Activation

1. Review the original and draft together for any local contract not captured
   above. The draft reduction is a proposal, not proof of semantic equivalence.
2. Update the playbook's `references/best-practices.md` and docs reference where
   they still imply all tests/docs/diagrams are required for every change.
   Preserve the principle of relevant behavior proof and documented checks.
3. Regenerate playbook `agents/openai.yaml` if its scope/description changes.
4. Correct the dashboard token-canon instruction and reconcile nested docs
   routing. Do not silently remove incoming routes to moved documents.
5. Decide the browser fallback and chart skill registration explicitly through
   the existing registries. The guidance draft does not enable/disable tools.
6. Bootstrap affected client surfaces and run required checks after canonical
   edits. The audit itself does not need to render these drafts.

## Pilot Prompts and Acceptance

| Representative task | Expected behavior |
| --- | --- |
| Correct a typo in a repo reference | Read enough context to preserve meaning; no unrelated skill hunt, full app suite, or new tracker. |
| Change a WIN provider retry path | Load provider/media contracts, run focused failure-path checks and required repo gate; preserve duplicate protection and cleanup. |
| Change a frontend-consumed WIN/AIP DTO | Follow both repos' actual contract-sync boundary, complete the authorized integration and verification without an artificial Phase 2 checkpoint. |
| Improve a small UI component | Apply the correct visual identity; inspect the changed surface and affected layouts without imposing a whole-product screenshot tour. |
| Resume a multi-session project | Use the current tracker, finish the scoped job and evidence, preserve genuine blockers, archive only on supported completion. |
| Work in a parked repo | Preserve its parked/runtime-disabled boundary; perform authorized offline work without restarting services. |
| Inspect an unavailable optional capability | Use available alternatives or report the missing dependency precisely; do not install or stop unrelated work automatically. |

Record the relevant files/skills loaded, unnecessary user stops, verification
performed, outcome correctness, and any lost invariant. Compare representative
tasks before and after activation where practical. Length reduction is secondary
to reliable completion.

## Rollback

Apply a small reviewed canonical change through the existing bootstrap. If a
pilot reveals a missing boundary, restore the original revision or add the
specific lost contract at its owning layer and re-render. Do not compensate by
copying the full old instructions into every repo.

## Independent Review Resolution

An independent review compared the drafts with canonical sources and the Dobby
ownership model. Four findings were incorporated: retain archive-before-final
handoff or an explicit blocker; restore the original clean-migration default
without adding an inferred consumer-compatibility exception; retain temporary
generated-file troubleshooting followed by a canonical fix; and state the
deterministic/local/quick/actionable fast-gate contract. See
`guidance-proposal-independent-review.md` for the review as originally recorded.
