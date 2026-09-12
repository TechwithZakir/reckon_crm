# Phase 0 acceptance

Record results separately for Frappe 15 + compatible CRM, Frappe 16 + compatible
CRM, and the latest supported Frappe/CRM pairing. Never infer these results from
source compilation alone.

## Local automated checks

- [x] Registry validation, duplicate detection, disposal, and desktop/mobile filtering.
- [x] Incompatible source anchors stop integration.
- [x] Compile Reckon Vue components and all four transformed detail pages.
- [x] Compile actual main and develop CRM adapter targets at README revisions.
- [x] Dependency guard accepts Frappe 15+, requires CRM, does not require ERPNext/HRMS.
- [x] Renderer delegates access checks and boot to CRM; permission errors propagate.
- [x] Missing/stale build and disable flag fall back; unrelated pages are untouched.
- [x] Stable CRM frontend production build with Vite 5.4.21 and PWA 0.21.2.
- [x] Latest CRM frontend production build with Vite 8.2.0 and PWA 1.3.0.
- [x] Verify `page_renderer` exists on inspected Frappe 15, 16, and develop sources.

Local builds were run on Windows with Node 24.14.1 on 2026-09-11, using isolated
CRM source snapshots and their respective Vite/plugin versions. They are full
frontend builds, not Bench/site installation tests. Stable emits upstream large
chunk warnings and a missing GitHub brand-icon fallback warning; neither stops
the build. Framework source used for shared UI was the current develop snapshot.

## Live Bench acceptance — pending

### Evidence received from the deployed site

- [x] User-provided screenshot at `erpdev.reckon.tech` shows the desktop
  FIELD SALES section and Field Visits sidebar entry.
- [x] The same screenshot shows a CRM Lead's selected Visits tab and the
  expected empty state at a URL ending in `#visits`.
- [x] An unauthenticated request to `/crm/visits` displayed “Not Permitted”
  and a login link during browser inspection.

These observations verify only the listed behavior. They do not establish Deal,
mobile, PWA, restricted-user, disable/uninstall, or cross-version acceptance.
An authenticated browser session was subsequently used to verify `/crm/visits`
and its empty state after refreshing. The Deals list loaded but contained no
deals, so a Deal detail tab could not be verified without creating test data.
The browser hostname differs from the Bench site name reported by the user;
do not assume that they map to the same site without checking deployment configuration.

### Remaining acceptance checklist

- [ ] `bench --site SITE install-app reckon_crm` succeeds with CRM only.
- [ ] `bench build --app reckon_crm` succeeds and writes only Reckon assets.
- [ ] A guest and a logged-in user without CRM access cannot enter CRM.
- [ ] Existing Leads, Deals, Contacts, Organizations, activities and settings work.
- [ ] `/crm/visits` loads by sidebar navigation, refresh, and direct link.
- [ ] FIELD SALES / Field Visits appears on desktop and in the mobile drawer.
- [ ] Lead and Deal show Visits and the placeholder on desktop.
- [ ] Mobile Lead and Deal show Visits; Details and Activity still work.
- [ ] Back/forward navigation and `#visits` deep links work.
- [ ] Existing actions, native tabs, permission errors, and restricted records work.
- [ ] On HTTPS, PWA installation opens CRM and mobile layouts fit 360px width.
- [ ] Log out, switch users, and verify no previous user's CRM data is cached.
- [ ] Disable Reckon and verify the original CRM loads.
- [ ] Uninstall on a disposable site and verify the original CRM still works.
- [ ] Confirm `git status --short` inside the installed CRM has no source edits.

Do not mark Phase 0 complete until these live checks pass. The user subsequently
explicitly requested continuing to the next phases; Phase 1 development proceeds
under that instruction while the unverified checks remain recorded here.
