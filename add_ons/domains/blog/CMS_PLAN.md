# CMS Plan (Blog Add-on)

This document is the implementation plan for the **Blog** add-on to evolve into a lightweight CMS that fits the platform’s add-on architecture.

## Goals

- Provide a **B2C-friendly** blogging CMS that ships **enabled by default**.
- Keep the Blog domain **self-contained** (routes/services/ui), but leverage core platform services where possible (auth, settings, storage, search).
- Support a content workflow that works for:
  - Site owner (admin)
  - Supporting staff (admin/moderator/editor roles)
  - Authors/contributors
- Future CMS capabilities (later milestones):
  - Complex page-builder / drag-and-drop layouts /or post templates.
  - Full WYSIWYG with collaborative editing.
  - Headless CMS API surface (later)
  - Import/migration tools from third-party CMS platforms.

## Non-Goals (for initial milestones)

- Multi-tenant “many site owners” logic.
- Advanced personalization/recommendation engines.

## Current Scaffold Status

- Routes:
  - `GET /blog` list posts
  - `GET /blog/new` create form (auth required)
  - `POST /blog/posts` create
  - `GET /blog/posts/{post_id}` view
- Service:
  - `PostService` with demo in-memory storage and optional Mongo via `DBService`.

## Data Model (Target)

### Collection: `blog_posts`

Core fields:

- `id` (int)
- `author_id` (int)
- `title` (str)
- `slug` (str)
- `body` (str)
- `excerpt` (str)
- `status` (enum): `draft | scheduled | published | archived`
- `published_at` (datetime | None)
- `scheduled_for` (datetime | None)
- `created_at` (datetime)
- `updated_at` (datetime)

Optional fields:

- `featured_image_url` (str | None)
- `tags` (list[str])
- `category_ids` (list[int])
- `seo` (object)
  - `title` (str | None)
  - `description` (str | None)
  - `canonical_url` (str | None)

### Collection: `blog_categories`

- `id` (int)
- `name` (str)
- `slug` (str)
- `created_at` (datetime)

### Collection: `blog_revisions`

- `id` (int)
- `post_id` (int)
- `editor_id` (int)
- `body` (str)
- `created_at` (datetime)

## Roles & Permissions (Target)

- `blog_admin` (inherits `admin`)
  - Full access to posts, categories, settings
- `blog_editor`
  - Edit/publish others’ posts, manage categories
- `blog_author` (inherits `member`)
  - Create/edit own posts

Notes:

- We should use the existing permission system patterns (`Role`, `Permission`).
- The first iteration can enforce only **auth required** + ownership checks; expand to permissions once workflows solidify.

## UI / UX Plan

### Public

- Blog index (`/blog`)
  - featured post + list
  - pagination
  - tag/category filters
- Post detail (`/blog/posts/{id}` and later `/blog/{slug}`)

### Authoring

- Author dashboard (`/blog/admin`)
  - list: drafts/scheduled/published
  - quick actions: edit, publish, archive
- Editor
  - initially: markdown textarea
  - later: markdown preview split view

### Moderation / Staff

- Review queue
  - drafts awaiting approval (optional)
  - audit log (basic)

## API / Route Milestones

### Milestone 1: Solid CRUD (MVP)

- `GET /blog` list published posts only
- `GET /blog/posts/{id}` show published; allow drafts for author/admin
- `GET /blog/new` + `POST /blog/posts`
- `GET /blog/posts/{id}/edit` + `POST /blog/posts/{id}`

### Milestone 2: Workflow

- Post status transitions:
  - draft -> published
  - draft -> scheduled
  - published -> archived
- Add `published_at` and `scheduled_for` enforcement
- Background job hook (optional) for scheduled publish

### Milestone 3: Taxonomy

- Categories + tags
- Filter pages:
  - `/blog/tags/{tag}`
  - `/blog/categories/{slug}`

### Milestone 4: Media

- Featured image upload via core storage integration
- Inline image attachments (later)

### Milestone 5: SEO + Sharing

- Slug routes `/blog/{slug}`
- Meta tags / OpenGraph
- Canonical URLs

### Milestone 6: Search + Analytics

- Search integration via existing SearchService (if available)
- Basic metrics:
  - views per post
  - referrers (optional)

### Milestone 7: Page Builder

- Page templates and reusable blocks
- Drag-and-drop layout builder (initially limited set of components)
- Per-page/per-post layout selection

### Milestone 8: Collaborative WYSIWYG

- Rich text editor (WYSIWYG)
- Presence/locking and conflict strategy
- Revision history UX built on `blog_revisions`

### Milestone 9: Headless CMS API

- Read APIs for posts/categories/tags
- Authenticated write APIs for staff/author tools
- Versioning strategy for API endpoints

### Milestone 10: Import / Migration Tooling

- Import from common CMS/export formats (start with a minimal subset)
- Mapping: authors, slugs, timestamps, tags/categories
- Dry-run mode + error report
- Idempotency strategy (avoid duplicate imports)

## Storage & Rendering Notes

- Keep blog content rendering deterministic:
  - sanitize HTML if we allow rich text
  - if markdown, render to HTML on read, or cache rendered HTML
- For now, simplest: store `body` as markdown and render server-side.

## Testing Strategy

- Unit tests for:
  - slug generation
  - status transitions
  - authorization rules
- Integration tests (optional) for:
  - create/edit/publish flow

## Open Questions

- Do we want the canonical post URL to be `/blog/posts/{id}` forever, or migrate to `/blog/{slug}` once slugs are stable?
- Should staff roles be platform-wide (site owner) or blog-scoped only?
- Do we want comments as part of Blog, or reuse Social comments later?
