Yes, to boot sequence:

- **`app/core/bootstrap.py` ** builds the app
- **`app/core/mounting.py`** mounts core router
- **app/app.py **runs bootstrap and mounting, and
- calls add on loader
  - if demo,
    - load blog and example apps (marketing pages/example fake checkouts, like they are now, not wired to make transactions with stripe).
  - if not demo,
    - load blog and other addons via manifest/.env values? (in production, they would need to be added to a given add on domain submodule repo and have some kind of key they can pass to loader as an arg)

For example apps: 

- contracts (example products, courses, streams, users) might be an early object in the manifest, and examples are just demo routers with data fixings that can mount to core) and still build from manifest in loader?


For integrations, i need to better distinguish between infrastructure integrations, shared integrations, and domain specific (Or not, and just put all integrations in app/core/integrations)

i agree that all imports should move to app.core

and yes a different default HomePage, editable/customizable by theme editor/web admin
