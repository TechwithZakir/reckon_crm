# Phase 1 — Field visits (0.3.0, unreleased)

## Deploy to the correct site

Frappe CRM must be installed first. A browser hostname is not necessarily the
Bench site name: the user reported `erp.reckon.tech` as an existing site while
using `erpdev.reckon.tech` in the browser. Verify that mapping before deployment.

After deploying this code into `apps/reckon_crm`, run from the Bench directory:

```sh
bench --site YOUR_SITE backup
bench --site YOUR_SITE migrate
bench build --app reckon_crm
bench --site YOUR_SITE clear-cache
bench --site YOUR_SITE execute reckon_crm.diagnostics.status
```

Restart production workers using your normal deployment procedure and reload
`/crm/visits`. Migration creates **CRM Field Visit** and **CRM Customer Location**.
Building alone does not create database tables. No ERPNext/HRMS installation is
required. Existing CRM roles are reused: Sales User, Sales Manager, System Manager.

Version 0.3.0 adds `calendar_event`, `crm_task`, `employee_checkin`, and
`employee_checkout` fields plus **Reckon CRM Settings**. Run migration even if the
visit DocTypes already exist. No upstream CRM files are modified.

## Settings, multi-user visits, and optional integrations

Only the **Administrator** account can open `/crm/visit-settings`. The Field Visits
header shows the Visit settings link only to Administrator. Direct URL access, the
settings API, and the Desk DocType are denied to other users. The switches are:

| Switch | Default | Behavior |
| --- | --- | --- |
| Calendar | On | Creates/updates a private native Event per visit. |
| CRM Task | Off | Creates/updates a native CRM Task per visit. |
| Employee Checkin | Off | On actual check-in/out, creates HRMS IN/OUT logs. |
| Skip auto attendance | On | Keeps HRMS visit logs out of auto attendance. |

Managers select one or more eligible users; each person receives a separate visit
record and can only check in/out their own record. The selector shows at most 100
eligible users and allows a maximum of 25 selected users. Scheduling is atomic:
an invalid user or failed enabled integration rolls back the submitted batch.

HRMS sync requires HRMS, an active Employee linked to each user, Employee Checkin
creation permission, and HRMS-compatible coordinate fields. Native HRMS shift,
geofence, duplicate log, and attendance checks run normally. Reckon does not import
HRMS unless the setting is enabled at runtime.

## Maps and native calendar sync

The scheduling form has an interactive Leaflet/OpenStreetMap map: pan, zoom, click
to select a customer location, see the geofence radius, or choose **Fetch
geolocation** to request browser location. Check-in/out details show captured
markers. The browser displays its own permission prompt; if permission was blocked,
allow Location in the address-bar site settings and retry Fetch geolocation.

Maps require internet access to `https://tile.openstreetmap.org`; no API key is
needed. A custom Content Security Policy must allow that host in `img-src`.
Coordinates remain usable if map tiles fail. There is no offline map, background
tracking, or anti-spoofing claim.

Leaflet is resolved from Frappe CRM's own frontend dependencies. If a build reports
that it is missing, run `cd apps/crm && yarn install`, return to the Bench directory,
then run `bench build --app reckon_crm` again. Do not install a separate Leaflet
copy under Reckon CRM.

Each newly saved visit creates one private Event owned by its creator, with the
assignee as a participant. Date-only visits span the day; start-only visits reserve
one hour. Times use the site's timezone. A planned visit can be rescheduled from
its native Desk form; saving updates the same Event, including changed assignees.
Completion marks the Event Completed; cancellation or deletion of a planned visit
marks it Cancelled. CRM Calendar's normal Open filter hides these finished Events.
Native Event permissions govern calendar visibility.
Administrator is not an email participant: its own Events use ownership. For a
visit another user assigns to Administrator, select the creator's calendar filter.

Sync is one-way. Change the visit rather than editing or dragging its Event in
Calendar; managed Event edits/deletes are rejected to prevent schedule divergence.
Open calendar uses the installed CRM Calendar route when present, falling back
to Desk Calendar for older CRM builds. Native Event fields were inspected in
[Frappe 15](https://github.com/frappe/frappe/blob/version-15/frappe/desk/doctype/event/event.json),
[Frappe 16](https://github.com/frappe/frappe/blob/version-16/frappe/desk/doctype/event/event.json), and
[develop](https://github.com/frappe/frappe/blob/develop/frappe/desk/doctype/event/event.json).
This source inspection does not certify a live installation.

For pre-upgrade Planned/Started visits, open their details and use **Sync to calendar**,
or save the visit. There is no automatic bulk backfill of old visits. Sync does not
enable Google/Outlook integration; existing native CRM notification settings apply.

## User workflow

1. Open Field Visits or the Visits tab on a Lead/Deal; click Schedule visit.
2. Choose a native CRM record, purpose, date/time, and optional customer location.
   Managers can assign an enabled CRM user who can read the linked record;
   other sales users schedule for themselves.
3. Optionally add a location with coordinates and an allowed radius of 1–10,000m.
   This requires write access to the CRM reference. Searching records currently
   matches their record IDs and returns at most 30 choices.
4. Open the scheduled visit. Check distance, then check in with a fresh location
   sample, or explicitly check in without location verification.
5. Upload a private attachment/photo before completion if needed. The standard
   Frappe Desk form also exposes an optional Signature field before completion.
6. Enter outcome, notes, and optional follow-up date; complete with or without a
   location sample. Completion posts a summary to the native CRM timeline.

Outside-radius and low-accuracy check-ins are **flagged, not blocked**. Accuracy
over 100m is classified as Accuracy Too Low. Missing coordinates are Location
Unavailable, and a sample without a customer location is Not Checked. Browser
GPS is not a reliable anti-spoofing mechanism. Only action-time samples are saved.
Checkout uses the location/radius snapshot captured at check-in, even if the
customer location is later edited.

## Access and lifecycle

- Native CRM record access is required for reads, lists, and writes. Field sales
  users can access their assigned visits; managers still need reference access.
- Only the assigned user can check in/out. Server timestamps and row locks protect
  transitions. Direct client edits cannot set status or derived audit fields.
- Planned visits can be cancelled. Completed, cancelled, and missed visits are
  immutable; only planned visits can be deleted, by a permitted manager.
- Completion and timeline comment are one transaction. Outcome is escaped before
  it enters comment HTML. Detailed visit notes are not copied into that comment.
- Normal Frappe Version records track changes. Lists use permission-filtered CRM
  IDs, which can be expensive on large sites; load-test before a large rollout.
- Photo/file uploads are private and must be attached to this visit. Review the
  site's existing file-size limits. A failed field attachment can leave the
  uploaded private file attached to the visit for review through Frappe.

## Validation and pending site checks

Local unit tests and production frontend compilation do not certify a running
database/site. Run the provided integration test on a **disposable test site**:

```sh
bench --site TEST_SITE run-tests --app reckon_crm --module reckon_crm.reckon_crm.doctype.crm_field_visit.test_crm_field_visit
```

Then verify manually on your intended deployment:

- [ ] Migration succeeds with Frappe CRM installed and ERPNext/HRMS absent.
- [ ] Status, All statuses, and Refresh stay in one row on desktop/mobile.
- [ ] Manual/current-location coordinates and saved location selection show the map.
- [ ] Scheduling creates one private Event visible to creator and assigned user.
- [ ] Reschedule/reassign in the visit Desk form updates the same Event; retries do not duplicate it.
- [ ] Completion/cancellation update Event status; managed Event direct edits are rejected.
- [ ] Sync to calendar works for an older active visit; denied Event creation leaves no new visit.
- [ ] Sales User can schedule, preview, start, and complete an assigned visit.
- [ ] A second sales user cannot read or change that visit; managers obey reference permissions.
- [ ] Double-click/retry cannot produce duplicate completion comments.
- [ ] Wrong-reference location and invalid GPS samples are rejected.
- [ ] Denied GPS, low accuracy, inside/outside radius, and zero coordinates classify correctly.
- [ ] Private attachment/photo uploads and completed-record immutability work.
- [ ] Native Lead/Deal Activity shows the completion after refreshing.
- [ ] Forms work on mobile, with HTTPS geolocation permission.

No day attendance, nearby-customer map, automated missed-visit job, notifications,
quote management, or AI is included. Follow-up dates are stored on visits; this
phase does not automatically create CRM Task records. Signature capture in the
CRM SPA is not yet included; the native Desk Signature field is available.
