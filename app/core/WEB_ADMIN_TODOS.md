# Web Admin TODOs (Add-on Management + Future Git Sync)

This document is the **current** TODO list for completing Web Admin add-on management.

It assumes the existing Web Admin workflow:
- Separate admin login (`/admin/login`)
- Admin dashboard (`/admin/dashboard`) implemented in `app/core/routes/auth.py` + UI in `app/core/ui/pages/admin_auth.py`
- Site/section editing + draft/publish workflow (state system) under `app/core/routes/admin_sites.py` and workflows in `app/core/workflows/*`

## Current State (Observed)

- **Admin entry points**
  - `GET /admin/login` and `POST /admin/auth/login`
  - `GET /admin/dashboard`

- **Site editing / theme editing**
  - Component management: `/admin/site/components`
  - Theme editor: `/admin/site/theme`
  - Draft/publish concepts exist (draft/published partitions via persister)

- **Add-on system**
  - There is a manifest-based loader in `app/core/addon_loader.py`.
  - The main app currently skips “auto route mounting” for add-ons (commented due to conflicts with mounted example apps).
  - The app factory currently mounts **Blog** by default for non-demo apps.

## Primary Goal

Add a first-class **Add-ons** panel to the Web Admin dashboard with switches to:
- Enable/disable add-ons per site installation
- Persist the configuration
- Apply it safely (initially restart-required; later hot-apply)

Then, in a later phase:
- Move `app/add_ons/domains/*` into **private git repositories**
- Toggling an add-on can **pull/sync** the domain as a **git submodule** (or equivalent) and mount it.

## Phase 1 — Dashboard UX (Switches + Status)

- **Add an “Add-ons” section to the dashboard UI**
  - Location: `app/core/ui/pages/admin_auth.py` (`WebAdminDashboard`)
  - Must show an add-on list with:
    - **name**
    - **installed** (present in codebase / available)
    - **enabled** (toggle)
    - **mount path** (e.g., `/blog`, `/stream`)
    - **version** (from manifest if installed)
    - **notes / warnings** (e.g., “restart required”)

- **Define the initial catalog of add-ons**
  - **Blog** (default)
  - **Stream**
  - **Social**
  - **Commerce**
  - **LMS**

- **Switch behavior (initial UX)**
  - **On toggle**:
    - Save config immediately
    - Show “Changes pending restart” banner
  - Provide a “Apply / Restart required” UX:
    - Either a button that triggers a controlled restart (future)
    - Or instructions + a visible “pending changes” indicator

## Phase 2 — Persistence Model (Authoritative Source of Truth)

Pick ONE authoritative persistence mechanism for add-on enable/disable state.

Recommended approach:
- **Persist to Mongo (or existing persister system)** similarly to site draft/published state.

Tasks:
- **Define an Add-on Config shape**
  - Example:
    - `site_id` (single site: `main`)
    - `addons`: map of `{addon_id: {enabled: bool, installed: bool, source: ..., pinned_version: ...}}`
    - `updated_at`, `updated_by`

- **Decide scope**
  - **Installation/global** (single site per install): simplest
  - Optional later: per-site if multi-site is introduced

- **Implement read/write API for config**
  - **Read**: used by dashboard to render toggle states
  - **Write**: invoked by toggle endpoint

- **Audit trail**
  - Record:
    - who toggled
    - when
    - what changed (diff)

Acceptance criteria:
- Admin toggles persist across server restarts.

## Phase 3 — Enabling/Disabling Semantics (Safe Application)

Initially, implement “restart-required” semantics (safer, simpler).

- **Restart-required mode (MVP)**
  - Toggle updates persisted config.
  - On app startup:
    - Read persisted add-on config.
    - Enable/mount only configured add-ons.

- **Define what “enabled” means**
  - **Routes mounted**: endpoints are reachable
  - **Roles/settings/components registered**: manifests loaded
  - **UI/nav integration** (optional per add-on)

- **Define what “disabled” means**
  - Routes not mounted
  - Add-on UI hidden
  - Payments/webhooks for that add-on should be disabled or no-op

- **Avoid partial enablement**
  - Enabling should be atomic per add-on (either fully enabled or not).

Acceptance criteria:
- With `enabled=false`, users cannot reach add-on routes.
- With `enabled=true`, routes are mounted and core integration is functional.

## Phase 4 — Route Mounting Strategy (Resolve Current Conflicts)

Right now auto add-on mounting is skipped to avoid conflicts with example apps.

Tasks:
- **Separate “example apps” from “real add-ons”**
  - Example apps are mounted at `/eshop-example`, `/lms-example`, etc.
  - Add-ons should mount at their canonical routes (`/blog`, `/stream`, `/social`, …)

- **Create a dedicated add-on mount step**
  - Ensure it runs only for the “real” site app, not the example apps.
  - Make sure route prefixes do not collide.

- **Define mounting API per add-on**
  - Convention:
    - each domain exports `router_<domain>` (like `router_blog`)
    - mount with `router_<domain>.to_app(app)`

Acceptance criteria:
- Example apps still work.
- Enabled add-ons mount cleanly without conflicts.

## Phase 5 — Permissions & Access Control

- **Admin-only configuration**
  - Only `admin` / `super_admin` can toggle add-ons.

- **Granular staff permissions (optional)**
  - Add `site_admin` / `support_staff` roles later.
  - Allow some staff to view config but not change it.

- **Guard rails**
  - Blog cannot be disabled if it’s considered “core” for the product (decide policy).
  - Warn before disabling add-ons that have active purchases/subscriptions.

## Phase 6 — Operational Safety / Observability

- **Visibility**
  - Show current enabled set in dashboard.
  - Show last applied revision.

- **Logging**
  - Log every toggle and apply operation.

- **Rollback**
  - “Revert to previous config” button (uses stored history/audit entries).

## Phase 7 — Private Repo + Submodule Sync (Future)

This is the “real” system you described: toggling downloads/syncs domain code.

### Repository Model

- **Add-on registry metadata**
  - `addon_id`
  - `repo_url` (private)
  - `default_ref` (branch/tag)
  - `pinned_commit` (optional)
  - `integrity` (signed tags/commits if feasible)

### Sync Mechanics

- **Initial implementation (recommended)**
  - “Install” action separate from “Enable”:
    - Install = fetch code
    - Enable = mount code on next restart

- **Submodule operations**
  - Add submodule under `app/add_ons/domains/<domain>`
  - Pull/sync to desired ref
  - Record the exact commit hash in persisted config

### Security & Supply Chain

- **Credential management**
  - Use deploy keys or GitHub App tokens.
  - Never store secrets in repo.

- **Allowlist**
  - Only allow repos from a configured allowlist.

- **Verification**
  - Optional: verify signed commits/tags.

### Failure Modes

- **If sync fails**
  - Do not partially install.
  - Keep previous installed version.
  - Show actionable error in UI.

- **If enabled but missing**
  - Treat as “not installed” and show warning.

Acceptance criteria:
- Admin can install/sync add-ons from private repos.
- Enable state persists and is applied safely.
- Clear rollback path to a previous known-good commit.

## Phase 8 — Developer Experience / Packaging (Future)

- **Add-on interface contract**
  - Standard exports: `manifest`, `router`, optional `register_*` hooks
  - Optional compatibility checks: platform version constraints

- **Migration hooks**
  - On enable: run migrations (if any)
  - On disable: keep data but stop serving

## Open Decisions

- **Canonical filename/location**
  - This doc is `app/core/TODOS.md` so it stays close to the admin workflow code.

- **Source of truth**
  - State system vs settings service vs dedicated add-on config collection.

- **Apply strategy**
  - Restart-required first vs hot-mount/unmount.
