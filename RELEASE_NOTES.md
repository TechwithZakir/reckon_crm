# Reckon CRM release notes

All implemented features, changes, and fixes are recorded here. Unreleased work
is not a published release. Preserve previous entries when adding new versions.

## Unreleased

### Visit action visibility

#### Fixed

- Visit rows now explicitly show Open visit / Check in, Check out, or View details,
  according to status and the current assignee. Started visits show Check out.
- Opening a visit closes scheduling, scrolls to the details and moves keyboard
  focus there. Added loading feedback and guarded against stale detail responses
  when switching CRM records or opening another visit.
- Display saved check-in and check-out coordinate maps in visit details and explain
  when the current user is not the assignee. Location errors now distinguish denied
  permission, timeout and unavailable positioning, with browser-permission guidance.
- This change does not deploy the code or complete the requested multi-user,
  settings, task/HRMS sync, map redesign and native-theme improvements.

#### Validation

- 10 frontend tests and the production build passed locally. Live site behavior
  and real device permission prompts remain pending verification.

### Visit scheduling improvements (0.2.1)

#### Added

- OpenStreetMap previews in the new customer location form and for the saved
  location selected when scheduling a visit. Maps update with valid coordinates,
  include a marker, zoom controls, and a larger-map link; invalid/empty coordinates
  show guidance. This is a preview, not a map-based coordinate picker.
- Automatic one-way sync from saved visits to private native Frappe Events.
  The scheduling user owns the Event and the assignee is a participant. Schedule,
  purpose, assignee, completion, and cancellation changes reuse the linked Event.
- Date-only visits become all-day Events; timed visits without an end reserve
  one hour. Deleting a planned visit cancels its Event.
- A Sync to calendar action for older active visits without an Event, plus an
  Open calendar link using CRM Calendar when available and Desk Calendar otherwise.
- Unit coverage for calendar date ranges, reuse, permissions, protected links,
  incompatible schemas, failed creation, and map coordinate bounds. Expanded the
  disposable-site integration tests for Event creation, rescheduling and cancellation.

#### Changed

- Package version is 0.2.1. Added a protected Calendar Event link and migration
  diagnostics for that column. Event sync and visit saves use the same transaction.
- Calendar Events derived from visits must be edited through their visit; direct
  Event edits/deletes are rejected. Ordinary native Events remain editable.
- Updated the deployment guide with map hosting requirements, calendar behavior,
  prerequisites, and live acceptance checks.

#### Fixed

- Aligned Status, All statuses, and Refresh on one horizontal row.
- Reject an end time without a start time, avoiding ambiguous calendar ranges.
- Avoid putting the special Administrator user ID into native Email fields.

#### Validation and deployment

- 32 local Python tests and 10 frontend tests passed. Production build against
  inspected CRM develop passed. Browser inspection confirmed filter alignment
  and a loaded map marker using synthetic coordinates, without live CRM writes.
- Frappe Event schemas inspected on version-15, version-16 and develop; runtime
  checks reject missing required fields. Live version compatibility, migration,
  assignment visibility and calendar transactions remain unverified.
- After deploying the code, migrate the correct Bench site, rebuild Reckon CRM,
  clear cache, and restart workers. Frappe CRM must already be installed. Users
  scheduling visits need native Event creation permission; missing permission or
  Event failures roll back the visit save rather than silently skipping sync.
- Map previews require internet access to OpenStreetMap and send coordinates
  to that provider; no API key or new dependency is needed. A restrictive CSP must
  permit frames from https://www.openstreetmap.org. There is no offline map.
- Existing visits are not bulk-modified: active visits sync on their next save
  or through Sync to calendar. Google/Outlook sync is not enabled. Native CRM
  notification settings continue to apply; this change adds no notification jobs.
- Administrator's own Events use ownership, not an email participant. When another
  user assigns a visit to Administrator, use the creator's calendar filter to see
  that Event; ordinary email-based assignees appear in their own calendar.

### Phase 1 — Field Visit engine (0.2.0)

#### Added

- CRM Field Visit and CRM Customer Location DocTypes using native CRM Lead,
  CRM Deal, and CRM Organization references, with CRM sales-role permissions.
- Scheduling, manager assignment, visit list/history, detail controls, customer
  location creation, and status filtering in `/crm/visits` and Lead/Deal tabs.
- Server-owned check-in/check-out timestamps, actors, duration, coordinate and
  accuracy capture, customer-coordinate/radius snapshots, and Haversine distance.
- Server geo preview and explicit unverified check-in/out when GPS is unavailable.
  Outside-radius and accuracy-over-100m samples are flagged rather than blocked.
- Completion outcome, notes, follow-up date, private photo/file upload, and a
  native CRM timeline completion comment in the same transaction. The native
  Desk form includes an optional Signature field; SPA signature capture is deferred.
- Assigned-user and native CRM reference permission enforcement for APIs and Desk
  lists, immutable closed visits, and parameter-safe list permission conditions.
- Unit tests for geofences, lifecycle, actor/reference permissions, direct audit
  mutation, and list restrictions, plus a disposable-site integration test.
- Migration readiness diagnostics and the Phase 1 deployment/acceptance guide.

#### Changed

- Replaced Phase 0 empty placeholders with the visit workspace and forms.
- Advanced Python/frontend package versions to 0.2.0; unreleased work is not a
  published package or deployed-site certification.
- Recorded the user's explicit instruction to proceed with Phase 1 while retaining
  unverified Phase 0 site checks. ERPNext and HRMS remain optional and unused.
- Build metadata now records the extension version so deploying new server code
  cannot silently activate an old Reckon frontend bundle.

#### Fixed

- Direct JSON flags cannot authorize protected lifecycle changes: transitions use
  a server-only identity token, with row locks and state checks on mutation.
- Corrected mocked-module isolation so the expanded Python suite runs together.
- Reject public, external, and unrelated attachment links on direct DocType saves.
- Handle malformed metadata safely and report missing migrations and builds independently.
- Scope visit definition styles and box sizing to prevent layout overflow or changes to native CRM panels.

#### Validation and limitations

- 27 local Python tests and 9 frontend validation/compilation tests passed on
  2026-09-12. A full production build against inspected CRM develop passed.
- Both adapter compilation checks against the inspected CRM main/develop refs passed;
  this is not live certification of every Frappe 15/16/latest combination.
- Local browser smoke test with simulated records passed scheduling, check-in
  without GPS, completion, and the completed read-only presentation. This does
  not validate the deployed API or database.
- Live database tests, migrations, concurrent requests, mobile geolocation, file
  permissions, and native timeline behavior on the deployed site remain pending.
- Lists currently show the latest 100 accessible visits. Reference ID search
  returns 30 choices; large-site permission queries require load testing.
- No automatic missed visits, follow-up tasks, notifications, My Day/maps,
  HRMS/ERPNext integration, quotations, or AI are included in this phase.

### Live acceptance evidence

#### Changed

- Recorded the deployed screenshot confirming the desktop Field Sales sidebar
  and CRM Lead Visits empty state, plus the observed guest access denial.
- Kept the other live checks pending; the user authorized Phase 1 development.
  The screenshot does not certify Deal, mobile, PWA, or uninstall behavior.

### Installation troubleshooting — 2026-09-11

#### Added

- Administrator-only Bench diagnostic command, `reckon_crm.diagnostics.status`,
  reporting missing site prerequisites, renderer hooks, frontend assets, invalid
  metadata, disabled configuration, and stale CRM source fingerprints.
- Installation output now explicitly reports whether Reckon's frontend is ready
  and gives the build command when it is inactive.
- Troubleshooting instructions explain the build/cache checks and that Phase 0
  appears inside `/crm`, without a separate Desk workspace.

#### Fixed

- Frontend activation failures now have diagnostic reasons instead of only a
  boolean fallback result. The original CRM fallback is preserved.
- Disabled sites receive the enable command instead of an unnecessary rebuild
  instruction; missing hook lists and empty build IDs are handled safely.

#### Validation

- All 10 Python adapter tests passed, including four new tests for diagnostic
  outcomes, stale/missing assets, and installation messages.
- `git diff --check` passed. No frontend changes required a new frontend build.

#### Limitations

- The reported installed-site issue is not yet reproduced: its Frappe/CRM versions
  and build output are needed to identify the actual cause. These local changes
  have not been deployed to that site.

### Phase 0 — extension proof of concept

Recorded on 2026-09-11. Current package version: `0.1.0`.
Implementation and local validation are complete for the items below; live
Bench acceptance remains pending.

### Added

- Frappe app scaffold for `reckon_crm`, package metadata, module declaration,
  installation hooks, and GPL-3.0-or-later license.
- Frappe CRM prerequisite enforcement through `required_apps = ["crm"]` and
  an installation check. Frappe CRM must already be installed on the target site.
- Installation guard requiring Frappe 15 or newer. ERPNext and HRMS remain optional.
- Internal extension registries for CRM tabs, routes, sidebar items, and actions,
  with input validation, duplicate detection, and registration disposal.
- `/crm/visits` and the `FIELD SALES → Field Visits` sidebar entry.
- Visits tabs for native CRM Lead and CRM Deal on desktop and mobile, showing
  “No visits found. Schedule your first visit.” Scheduling is not yet implemented.
- Responsive empty-state components and visit icon.
- Vite adapter that extends the installed CRM source in memory without changing
  upstream files. Desktop/mobile integration and build coupling are isolated
  inside the adapter layer.
- Compatibility preflight, source fingerprints, and rejection of incompatible
  source anchors or an existing upstream `/visits` route.
- Narrow website renderer that reuses CRM's access checks, redirects, and boot
  data. Authenticated HTML uses `Cache-Control: no-store, private`.
- Fallback to the original CRM renderer when Reckon is disabled, assets or
  metadata are missing, or the checked CRM source fingerprints no longer match.
- `reckon_crm_disabled` site configuration flag and website-cache clearing hooks
  for installation, migration, and uninstall.
- Separate build directories that retain previous assets during rebuilds, with
  generated boot templates and compatibility metadata.
- Reckon PWA manifest and static-asset caching. No authenticated HTML or API
  response caching, offline record editing, or background GPS tracking.
- Frontend registry and adapter tests, actual upstream Vue compilation tests,
  Python installation/renderer contract tests, and GitHub Actions checks.
- Installation, architecture, disable/uninstall, compatibility, and acceptance
  documentation, plus a preserved copy of the supplied phased project plan.
- This separate release notes file, linked from the README, and a persistent
  repository rule requiring updates for every feature, change, and fix.

### Changed

- Build dependency resolution uses the installed CRM frontend's toolchain so
  Reckon can compile with its host's Vue, Vite, and Frappe UI versions.
- Build activation checks for CRM boot data and Reckon asset paths before
  publishing the generated template.
- Compatibility reporting distinguishes the Frappe 15/16/latest target from
  verified source/build checks and still-pending site acceptance.

### Fixed

- Import-only package exports now resolve through the host package loader,
  fixing the Frappe UI Vite plugin loading failure.
- Tailwind configuration uses Tailwind's loader, fixing extensionless plugin
  imports during production builds.
- Route validation rejects malformed paths, including protocol-relative paths,
  and detects conflicting registry names and paths.
- Disposing an old registration cannot remove a newer entry with the same key.
- Adapter test fixtures now use a valid Vue tab-slot parent for compilation.

### Validation

- 17 automated checks passed: 9 frontend tests, 2 upstream source compilation
  tests, and 6 Python contract tests.
- Stable CRM production frontend build passed with Vite 5.4.21 and PWA 0.21.2
  at CRM revision `52c500d6bdac3cd51553f95cfae9c7a940d99f1a`.
- Latest inspected CRM production frontend build passed with Vite 8.2.0 and
  PWA 1.3.0 at revision `73a209823730adb8d1f3e64ac471971f63362ca2`.
- Confirmed the renderer hook exists in the inspected Frappe 15, 16, and
  development sources. This is source verification, not site certification.
- Python wheel packaging passed.
- Compared 1,903 original CRM source files across the two build snapshots;
  none were changed.
- Local builds used Windows and Node 24.14.1, with current development Frappe
  shared UI source. Stable builds emitted upstream chunk-size and missing
  GitHub brand-icon fallback warnings without failing.

### Prerequisites and limitations

- Install a compatible Frappe CRM version on the site before Reckon CRM, and
  install that CRM version's frontend dependencies before building Reckon.
- Rebuild Reckon after upgrading CRM; unexpected source layouts require an
  adapter update. Historic and future CRM versions are not universally certified.
- Live Bench installation, authentication, browser navigation, mobile/PWA, and
  uninstall checks remain pending. See the [acceptance checklist](docs/phase-0-acceptance.md).
- No visit DocTypes, scheduling, geofences, quotations, business integrations,
  or AI features have been implemented. These belong to later phases.
- Action registration exists, but action rendering is deferred to Phase 1.
- No database migration is introduced in Phase 0. The repository has not been
  published or installed on a live site.
