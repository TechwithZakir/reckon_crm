# Phase 1 — Field visits (0.2.0, unreleased)

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
