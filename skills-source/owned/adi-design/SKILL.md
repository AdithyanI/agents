---
name: adi-design
description: Apply Adi's established visual identity to his personal apps and pages. Use for UI design or review involving house colors, typography, spacing, shape, motion, or design-token integration.
---

# Adi Design

Preserve Adi's recognizable identity: clean off-white rather than cream, functional sage accent with contextual amber, Newsreader for reading and Inter for UI, flat hairline surfaces, and restrained state-driven motion. Personal taste lives here; ordinary implementation decisions remain with the agent.

The canon is `~/GitHub/adi-design/system/`, with its version in `system/VERSION` and showroom at `https://design.adithyan.io`. `assets/tokens.css` is a vendored, flattened copy for use across repos. `system/styles.css` is an import manifest: copying it alone does not update the token bundle. When the canon changes, refresh from its imported `system/tokens/*.css` files in order and verify token values match.

Use existing token variables through the product's styling system. Keep app-specific additions in that app's local token layer. Edit shared identity in the canonical design repo, then update this vendored copy and affected rationale together; do not change token values only here.

For aesthetic rationale, contrast/typography constraints, or a product-specific integration decision, read `references/design-language.md`. Preserve the distinction between accent fill and contrast-safe ink depths; the reference explains consumers that collapse them into one primary color.

`impeccable` can supply frontend craft and `adi-writing` can supply voice. They do not replace the established palette or identity. Existing product tokens and design context should point to this canon; a routine UI refinement does not require creating another design document.
