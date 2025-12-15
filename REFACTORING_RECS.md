# Refactoring Recommendations (Keep Features, Simplify Tree)

This document proposes a **phased refactor plan** to simplify the project’s file tree **without removing features or changing behavior**. The goal is to reduce cognitive load, improve consistency, and prepare the codebase for future add-on syncing (private repos/submodules) and web-admin add-on management.

## Goals

- Preserve existing behavior and routes.
- Make “where to put code” obvious.
- Reduce duplicated / overlapping concepts (e.g., multiple “services” folders).
- Make the add-on story cleaner (domain add-ons vs example apps).
- Improve maintainability and testability without a “big bang” rewrite.

## Non-Goals

- Re-implementing features.
- Changing UI frameworks.
- Changing DB vendors.

## Current Pain Points (Observed)

- **Overlapping layers**
  - `app/core/services/*` (business logic) vs `app/add_ons/services/*` (mostly integrations/providers) creates confusion.

- **Routes vs add-ons vs examples**
  - Core routes are in `app/core/routes/*`.
  - Example apps are mounted under `/eshop-example`, `/lms-example`, etc.
  - Domain add-ons live in `app/add_ons/domains/*`.
  - The system has both a manifest-based add-on loader and “mounted example apps”, which is currently the main source of perceived complexity.

- **Entry points**
  - The runtime entry is `app/app.py`, but there is also `app/core/app_factory.py` used for constructing app instances.

- **Docs drift**
  - Lots of docs can become stale quickly; keeping a smaller set of authoritative docs reduces confusion.

- **Import / packaging model**
  - The repository uses `from core...` style imports, while code lives under `app/core/...`. This works today because of `sys.path`/runtime path handling, but it’s a common source of onboarding friction.

## Guiding Principles

- **Refactor in layers**: introduce new structure first, then gradually migrate call-sites.
- **Compatibility shims**: keep old imports/paths working during migration.
- **One canonical place** for each concept:
  - business services
  - integrations
  - routes
  - workflows
  - domain add-ons

---

## Phase 0 (No behavior change) — Normalize naming + document “where things go”

1. **Adopt a canonical taxonomy**
   - **Core**: platform infrastructure + shared business services
   - **Domains**: add-ons/bounded contexts (blog/stream/social/commerce/lms)
   - **Examples**: demo apps only

2. **Add and maintain “source-of-truth” docs**
   - `ARCHITECTURE.md`, `CODEBASE_INDEX.md`, `FILE_MANIFEST.md`
   - `app/core/WEB_ADMIN_TODOS.md`
   - `app/core/TEST_PLAN.md` (if you choose to keep it)

3. **Standardize file naming patterns**
   - Adapters already follow `*_adapter.py`. Keep that convention everywhere.

Deliverable: no code movement; just consistent terminology and small doc updates.

---

## Phase 1 (Low risk) — Consolidate “Integrations” and reduce duplication

### Problem
You effectively have two integration layers:
- `app/core/integrations/*` (Stripe, storage, email, etc.)
- `app/add_ons/services/*` (event bus, graphql, db abstractions, etc.)

### Recommendation
Create a single canonical home for infrastructure clients/providers.

#### Option A (preferred): Move `app/add_ons/services/*` into `app/core/integrations/*`
Example mapping:
- `app/add_ons/services/graphql.py` -> `app/core/integrations/graphql.py`
- `app/add_ons/services/event_bus_base.py` -> `app/core/integrations/event_bus/base.py`

Keep temporary re-export modules so existing imports continue to work.

#### Option B: Rename `app/add_ons/services/` to `app/integrations/`
This makes “integrations” top-level and keeps “core” narrower.

Deliverable: one integrations directory, old imports still work.

---

## Phase 2 (Low/medium risk) — Make the add-on story explicit

### Problem
Right now there are three related concepts:
- domain add-ons (`app/add_ons/domains/*`)
- example apps (`app/examples/*`)
- loader config (`app/core/addon_loader.py`)

### Recommendation
1. **Treat example apps as demos only**
   - Keep them mounted under `/...-example`.
   - Ensure add-ons use canonical routes (`/blog`, `/stream`, etc.).

2. **Introduce a stable add-on contract** (document-only first)
   - Each add-on exports:
     - `manifest` (id/version/roles/settings)
     - `router_<domain>` (routes)
     - optional `register_*` hooks

3. **Add-on catalog file** (for web-admin switches)
   - A single catalog describing:
     - mount path
     - repo source (future)
     - “core-required” flags (e.g., blog required)

Deliverable: less ambiguity around “domain addon vs example app”.

---

## Phase 3 (Medium risk) — Simplify entry points

### Problem
There is both:
- `app/app.py` (main app init)
- `app/core/app_factory.py` (factory)

### Recommendation
Establish one canonical boot sequence:

- **`app/core/bootstrap.py`**
  - build adapters/services
  - attach to `app.state`

- **`app/core/mounting.py`**
  - mount core routers
  - mount enabled add-ons
  - mount example apps (only in demo mode)

- **`app/app.py`** remains the executable entry point and calls into bootstrap + mounting.

Deliverable: smaller top-level `app/app.py` and clearer startup flow.

---

## Phase 4 (Medium risk) — Clarify routing conventions

### Recommendation
- Maintain `app/core/routes/*` as the only core router location.
- For each domain add-on:
  - keep `routes/` under the domain
  - export a single `router_<domain>` from `app/add_ons/domains/<domain>/routes/__init__.py`

Deliverable: consistent router export + mounting.

---

## Phase 5 (Medium/high) — Packaging & imports cleanup (optional)

### Problem
Imports assume a top-level `core` module even though it lives under `app/core`.

### Options
- **Option A (minimal):** keep current import behavior and document it.
- **Option B (clean):** make the project an installable package so `core` resolves without sys.path hacks.
  - Example: move to `src/` layout or package `app/` properly.

Deliverable: fewer path tricks, better IDE support.

---

## Phase 6 (Future) — Add-on repos + submodules (ties to Web Admin)

- Split each domain add-on into a private repo.
- Use submodules under `app/add_ons/domains/<domain>`.
- Web Admin toggles:
  - Install (sync repo) vs Enable (mount on restart)
  - pin commits + rollback

Deliverable: clean operational model for “optional add-ons”.

---

## Suggested Target Tree (Illustrative)

This is not meant as an immediate change, but a direction.

```
app/
  app.py
  core/
    bootstrap.py
    mounting.py
    addon_loader.py
    routes/
    services/
    workflows/
    ui/
    integrations/
  add_ons/
    domains/
      blog/
      stream/
      social/
      commerce/
      lms/
  examples/
    eshop/
    lms/
    social/
    streaming/
```

## Safety Checklist for Any Move

- Add compatibility re-exports before moving call-sites.
- Update `CODEBASE_INDEX.md` and `FILE_MANIFEST.md` in the same PR.
- Run unit tests + integration tests (docker compose up -d).
- Avoid changing runtime paths and mount points in the same step as file moves.

## Status

This file is a recommendation/plan only; no refactor is performed by creating it.
