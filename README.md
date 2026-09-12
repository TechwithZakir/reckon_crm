# Reckon CRM

Reckon CRM extends the existing Frappe CRM experience at `/crm`.
It uses native CRM Lead, CRM Deal, CRM Organization, Contact, activities,
communications, and tasks. ERPNext and HRMS are optional future integrations.

**Current milestone: Phase 1 Field Visit engine (0.3.0, unreleased).** Visit
scheduling, multi-user assignments, configurable Calendar/CRM Task/optional HRMS
sync, interactive customer maps, action-time GPS, check-in/check-out, and history
are implemented locally. Deployment and database acceptance remain pending.
The user authorized Phase 1 development while remaining Phase 0 checks stay open.
Quotations, My Day, and AI belong to later phases.

See [release notes](RELEASE_NOTES.md) for implemented features, changes, fixes,
validation results, and known limitations. Update them with every change set.

## What this adds

- `/crm/visits` inside CRM's existing router and application layout.
- `FIELD SALES → Field Visits` in the existing sidebar, including its mobile drawer.
- A `Visits` tab on Lead and Deal pages, on desktop and mobile.
- Schedule separate visits for up to 25 eligible CRM users against CRM Lead,
  CRM Deal, or CRM Organization, with date/time, purpose, and customer location.
- Interactive OpenStreetMap view with zoom/pan, click-to-select customer location,
  geofence radius display, and captured check-in/check-out markers.
- System Manager settings to enable Calendar Events, CRM Tasks, and optional HRMS
  Employee Checkin IN/OUT logs independently. All optional sync paths are off
  except Calendar by default; HRMS remains optional.
- Server-calculated geofence previews and check-in/check-out, including explicit
  unverified operation when GPS is unavailable. No background tracking.
- Immutable completed visits with outcome, notes, follow-up date, duration,
  private attachments/photos, and a native CRM timeline completion comment.
- Internal `registerCRMTab`, `registerCRMRoute`, `registerCRMSidebarItem`, and
  `registerCRMAction` APIs. These are Reckon APIs, not upstream extension APIs.
  The Schedule visit action is rendered in the Visits tab and Field Visits page.

**Existing installations:** follow the [Phase 1 deployment guide](docs/phase-1-deployment.md).
Run `bench --site YOUR_SITE migrate` before using the new APIs, then rebuild assets.

## Compatibility

The target is **Frappe 15, 16, and the latest release**. Use a Frappe CRM version
that itself supports your Frappe version. This is not a claim that every historic
CRM release or future upstream change works without an adapter update.

The adapter has source checks, Vue compilation checks, and successful production
frontend builds against:

| CRM branch | Inspected revision | Upstream Frappe declaration |
| --- | --- | --- |
| main | `52c500d6bdac3cd51553f95cfae9c7a940d99f1a` | `>=15.0.0,<17.0.0` |
| develop | `73a209823730adb8d1f3e64ac471971f63362ca2` | `>=16.0.0-dev,<=17.0.0-dev` |

Use the Node version required by the installed CRM frontend (the inspected
develop branch requires Node 20.19+ or 22.12+). Reckon's registry tests use Node
20.19 or newer. Python 3.10+ is required; follow Frappe's own requirements too.

## Install on an existing Bench

Run on a supported Linux/WSL Bench with Frappe CRM already installed. Do not
install Frappe itself with `pip install reckon_crm`.

```sh
bench get-app https://github.com/TechwithZakir/reckon_crm.git
bench --site YOUR_SITE install-app reckon_crm
bench build --app reckon_crm
bench --site YOUR_SITE clear-cache
```

The repository must first be pushed to that URL; this workspace has not been
published. To use a local checkout, use `bench get-app /absolute/path/to/reckon_crm`.

The root `package.json` exposes the build command used by Bench. The build reads
the adjacent `apps/crm/frontend` and resolves build dependencies from that
frontend. Install CRM's normal frontend dependencies using its documented Bench
workflow first. If your source lives elsewhere:

```sh
cd apps/reckon_crm
RECKON_CRM_SOURCE=/absolute/path/to/crm npm run check:compatibility
RECKON_CRM_SOURCE=/absolute/path/to/crm npm run build
```

After the build, open `/crm/visits`. A missing or incompatible build falls back
to the normal CRM page; it does not silently substitute a separate CRM app.

## How the extension works

The current CRM source has no public external route/tab/sidebar registry.
Reckon therefore uses a small Vite adapter to transform six upstream modules
**in memory** while compiling the installed CRM application. It imports the
Reckon registry and components into those modules. Upstream source files are
never written, copied into this repository, or maintained as a fork.

All source and build coupling lives in `frontend/src/extensions/adapters`.
Unexpected anchors stop the build. Assets are published only under Reckon's own
public directory, using distinct build directories so a failed rebuild leaves
the previous assets available. Keep previous build directories while active
browser sessions may still reference them.

A narrow Frappe `page_renderer` hook handles the already-resolved `crm` endpoint.
It calls **CRM's own `get_context()`** for access checks, redirects, CSRF boot,
translations, and session data. Authenticated HTML is returned with `no-store`.
The renderer checks the six source fingerprints and asset presence before
activating Reckon; rebuild after CRM upgrades. Phase 1 APIs enforce the normal
DocType and linked CRM record permissions; audit transitions remain server-owned.

The mobile layout, native navigation, and PWA build are retained. Reckon's
manifest opens `/crm`; its worker caches only static assets under its asset
scope. **Authenticated HTML and CRM API responses are not cached, and offline
record editing is not implemented.** HTTPS and live mobile installation testing
are required for deployment.

## Disable and uninstall

If installation succeeds but CRM looks unchanged, run from your Bench directory:

```sh
bench --site YOUR_SITE list-apps
bench build --app reckon_crm
bench --site YOUR_SITE clear-cache
bench --site YOUR_SITE execute reckon_crm.diagnostics.status
```

After updating a running production deployment, restart its Bench processes using
your normal deployment procedure and hard-refresh `/crm/visits`. Reckon adds
features inside `/crm`; it does not create a separate Desk workspace. The
diagnostic explains missing builds, disabled configuration, stale source, and
missing renderer hooks. A `ready` result checks activation prerequisites, not
the full browser acceptance checklist. On an older checkout without the diagnostic,
update the app code first; share any build error rather than assuming a build passed.

To temporarily use the original CRM build:

```sh
bench --site YOUR_SITE set-config reckon_crm_disabled 1
bench --site YOUR_SITE clear-cache
```

Set the flag to `0` to re-enable. To uninstall, use the normal Bench command:

```sh
bench --site YOUR_SITE uninstall-app reckon_crm
bench --site YOUR_SITE clear-cache
```

Removing the app removes its renderer hook. CRM's original assets and source
remain available. Test this on a disposable site before production rollout.

## Development and checks

```sh
npm ci
npm test
RECKON_CRM_SOURCE=../crm npm run test:upstream
# Within a Bench virtual environment (Werkzeug is provided by Frappe):
python -m unittest discover -s tests/backend -v
```

The Python tests mock Frappe to verify adapter contracts. They do not claim
database, login, routing, or uninstall integration coverage. Source tests compile
the real transformed Vue files; they do not replace browser tests.

See [the acceptance checklist](docs/phase-0-acceptance.md) and
[architecture notes](docs/architecture.md). Follow the supplied
[project plan](docs/project-plan.txt) one phase at a time.

## License

GPL-3.0-or-later. Frappe CRM and its assets retain their upstream copyright and
license notices. No upstream source is vendored in this repository.
