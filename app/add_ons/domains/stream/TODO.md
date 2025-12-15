# Stream Add-on TODO

This file tracks remaining work for the `stream` add-on.

## Product / UX

- **Stream landing UX**
  - Clarify the difference between live vs upcoming vs recordings on `/stream`.
  - Add filters/search (by title, host, date).

- **My events UX**
  - Improve `/stream/my-upcoming` to group by date and show start time clearly.
  - Add ability to "unattend" / remove RSVP.

- **Checkout UX**
  - Improve the PPV checkout flow (clear confirmation states, receipt page, and return-to-stream CTA).
  - Add a dedicated "access granted" page after membership purchase/PPV purchase.

## Paywall + Membership

- **Unify membership paywall UI**
  - Refactor the stream-specific "Become a member" modal into a reusable core component (deferred earlier).

- **Global membership strategy**
  - Decide and document how platform-wide membership tiers map to addon access.
  - Consider per-addon entitlements (e.g., blog premium, stream premium, etc.)

## Attendance

- **Data model hardening**
  - Enforce uniqueness: one attendance per (user_id, stream_id).
  - Add indexing strategy for Mongo collections.

- **Reminder/notification hooks**
  - Optional: email/push reminder before scheduled start.

## Streaming (WebRTC)

- **Signaling robustness**
  - Add server-side validation for SDP/candidate payload shape.
  - Better cleanup of abandoned viewer sessions (timeouts / TTL sweep).
  - Rate-limit signaling endpoints.

- **Multi-viewer scaling**
  - Add monitoring/limits for concurrent viewers.
  - Consider SFU integration if needed later (beyond current P2P approach).

- **Player experience**
  - Add reconnection logic and clearer error states on the UI.
  - Add a "waiting room" for upcoming streams.

## Chat

- **Moderation tools**
  - Streamer/admin delete message
  - Slow-mode / rate limits
  - Basic profanity filter hook (if enabled)

- **Persistence and pagination**
  - Ensure chat history paging is efficient for long streams.

## Stream Management

- **State machine**
  - Formalize stream states (draft/scheduled/live/ended/archived) and enforce transitions.

- **Scheduling rules**
  - Validate `scheduled_start` is in the future for scheduled events.
  - Timezone handling (store UTC, display local).

## YouTube Integration

- **Production hardening**
  - Proper OAuth refresh token flow (avoid manual access tokens).
  - Store YouTube broadcast metadata on the stream reliably.

## Tests / Quality

- **Unit tests**
  - Paywall rules (free vs paid, member vs PPV)
  - Attendance service behavior
  - Chat gating

- **Integration tests**
  - End-to-end: create scheduled stream -> attend -> watch -> chat

- **Observability**
  - Add structured logs around signaling, paywall decisions, and attendance.
