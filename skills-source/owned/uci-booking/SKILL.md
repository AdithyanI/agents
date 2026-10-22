---
name: uci-booking
description: Prepare, book, resume, or verify UCI cinema tickets for the user and their partner, applying both Unlimited Cards and an available linked payment method. Use for UCI checkout, seat selection, advance-booking card eligibility, and payment completion; public showtime discovery remains with the workspace cinema CLI.
---

# UCI Booking

Handle the ordinary two-person booking through existing tools. This is an
agent workflow, not an unattended checkout script or a supported booking API.
Do not add extra guests, split seating, or booking infrastructure unless asked.

## Context and tools

- Read the calling workspace's `docs/playbooks/outings.md` for the people,
  cinema, language, seating, and payment preferences. Keep personal details,
  credentials, card numbers, and receipts in their authorized private owner;
  never copy them into this shared skill.
- Use workspace-bound `./bin/dobby cinema showtimes` for current screenings and
  first-party booking links; `cinema seating recommend` / `assess` supplies
  static geometry, not live availability. Read `--help` for current flags.
  The engine's `docs/cinema.md` owns those command contracts.
- Use the available browser-control skill for the live checkout. Prefer the
  controllable in-app browser; preserve an explicitly chosen desktop Chrome
  session. Load the relevant browser/computer-use skill and follow its access
  and confirmation rules. Verify actual page control, not just ambient tab
  metadata. Do not replace a missing browser tool with hidden checkout APIs,
  browser-store inspection, or guessed endpoints.
- Reuse signed-in sessions or the authorized secret-management route. Missing
  tool access is not evidence of bad credentials. Do not recreate accounts,
  save payment details, or change account settings to make checkout work.

## Prepare the two tickets

1. Recover any existing checkout or receipt before opening another order.
   Match the live film, venue, auditorium, language/format and venue-local date
   and time. Preserve existing checkout tabs; a performance URL alone does not
   restore selected seats, account state, or a payment session.
2. Check the requested time against the calendar when choosing between dates.
   Default to two adjacent ordinary seats for the user and partner. Use the
   static seating guide plus current visual availability; do not substitute
   wheelchair bays or infer adjacency from consecutive seat numbers alone.
3. Select exactly two tickets and verify the live row/seat labels. Prefer one
   checkout using the holder's own Unlimited Card plus the partner's card via
   the second-card field when both are eligible.
4. Inspect the actual price after card application: each ticket, seat/format
   supplements, fees and combined total. Never substitute an old surcharge or
   a full-price ticket for a rejected card without approval. Keep the price
   breakdown clear even when the combined total looks inexpensive.

### Cards beyond their displayed term

Observed in completed UCI bookings on 2026-10-21; verify the current wording:

- Applying the signed-in holder's own card offered explicit consent to extend
  the subscription through the screening month. Applying another holder's card
  beyond its term instead returned a contract-end rejection, with no extension
  consent. Monthly-renewal email alone did not establish advance eligibility.
- If needed, use two isolated account sessions and one actual intended seat in
  each order, so each holder can apply their own card. Keep the pair adjacent.
  A normal new tab shares login cookies; it is not account isolation. Do not
  log the user out of their preserved checkout to sign in the partner.
- When moving a seat between checkouts, verify which order currently holds it
  and recheck availability, labels, counts and discounts after each change.
  Changing ticket count can clear the selected seats; navigation can briefly
  show stale cart totals. Wait for the settled state before continuing.
- Obtain approval for the actual subscription commitment before extending it;
  carry that approval forward for the same terms. Do not purchase a second
  subscription or extend to a different plan as a workaround.

## Pay and verify

- Use the user's available linked payment method; prefer their stated method
  when ready. A partner's cinema login does not authorize using the partner's
  funding source. Do not request new financial credentials when an authorized
  existing method works.
- Honor required action-time confirmations. Immediately before purchase,
  identify the exact showing, two seats, price for each order/combined total,
  and any subscription commitment. One confirmation may cover both clearly
  specified orders; a changed amount or material term needs fresh approval.
- UCI's payment-selection/review screens are not proof of PayPal authorization.
  In the verified flow, choosing PayPal led to review, then `JETZT KAUFEN`
  redirected to PayPal. If authentication needs the user, preserve both sessions
  and hand over the exact observed payment links with their amounts. Do not
  fabricate a payment link, solve a challenge, or claim payment succeeded.
- After payment or an uncertain redirect, inspect the UCI booking confirmation
  before retrying. For each order verify payment accepted, film/version,
  venue-local date/time, exact seat, charged amount and booking reference.
  Use the correct holder's mailbox through its workspace mail CLI if receipt
  recovery is needed; follow that workspace's mail playbook. If one order is
  confirmed and the other pending, report that distinction and resume only
  the unfinished one. Never rebook the paid seat merely because a tab changed.
- Return the verified outcome and ticket/receipt links, not an implementation
  log. Add a busy calendar block when requested or already authorized, using
  venue-local time; include the receipt references and label an estimated end
  or arrival buffer instead of inventing a runtime. Do not send invitations
  unless requested.
