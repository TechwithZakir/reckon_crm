# Phase 0 architecture decisions

## Boundaries

The installed Frappe CRM is the application foundation. Reckon only contributes
navigation and empty Visits panels in this phase. No ERPNext/HRMS dependency,
custom database schema, role provisioning, or external messaging is added.

The registry is independent of upstream component structure. Components contain
presentation only. The adapter translates registry entries into the host's
route records, sidebar sections, and detail tab shape.

## Why build-time integration

Desk `app_include_js` does not extend CRM's separately built Vue SPA. Loading a
script into the page cannot access its private router or component-local tab
arrays. Depending on undocumented Vue instance internals or mutating the DOM
would be fragile and violate the project requirements.

The chosen approach compiles the installed host source using a Vite `pre`
transform. This costs another frontend build, but makes the integration visible,
testable, and reversible without maintaining an upstream fork. The Python
renderer selects this build only for the CRM endpoint; all other website routes
continue through Frappe's normal renderer chain.

## Explicit assumptions

- Frappe supports `page_renderer`; CRM resolves `/crm/*` to `crm`.
- CRM exports `crm.www.crm.get_context()` with no required arguments.
- Router initialization contains one `const routes = [` anchor.
- The sidebar contains one `return _views` and one `<script setup>` block.
- Each Lead/Deal view has one `tabOptions.filter` return and one Activities panel.
- Mobile views render a `tab` slot with Details followed by Activities `v-else`.
- Current Frappe UI exports a `frappe-ui-lucide-icons` resolver. Older icon plugin
  versions require a separate adapter, not a guessed fallback.
- CRM's Tailwind config has an array of content paths.
- The host installs its own frontend dependency versions, including shared
  `@framework/ui` on versions that use it.

These are checked where possible during build. The source fingerprint guard
prevents continuing to use an old adapter after one of the six touched modules
changes. It does not certify unrelated backend changes; upgrades still require
the live acceptance checklist and a rebuilt bundle.

## PWA and security

Use CRM's own authentication/authorization, CSRF boot, and route guards.
No whitelisted methods or record writes exist in this phase. The future visit
API must enforce user and reference-record permissions on the server.

PWA assets remain same-origin. Service workers have asset-only scope, no
navigation fallback, and no API runtime cache. There is no offline CRM data
storage, continuous GPS tracking, or external AI provider call.

## Later phases

Do not begin the visit engine until Phase 0 is accepted on a real site. Phase 1
adds CRM Field Visit, CRM Customer Location, permission-aware APIs, server-side
Haversine geofences, lifecycle audit data, and native CRM activity integration.
Products, quotations, optional integrations, intelligence, and AI follow the
ordered phases in the supplied plan.
