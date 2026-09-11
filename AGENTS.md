# Reckon CRM

Reckon CRM extends Frappe CRM. Implement one phase at a time; do not start
Phase 1 until Phase 0 passes its live Bench acceptance checks.

- Never modify upstream CRM source or fork it.
- Use CRM Lead, CRM Deal, CRM Organization, and Contact as the foundation.
- ERPNext and HRMS remain optional. Do not import them in common modules.
- Keep frontend coupling inside `frontend/src/extensions/adapters`.
- Reuse native activities, email, calls, tasks, notes, WhatsApp, and Meta sync.
- Every API and DocType must enforce permissions and server-side validation.
- Calculate geofences and money on the server in their respective phases.
- No continuous background GPS tracking or browser anti-spoofing claims.
- Do not add speculative future-phase modules.
- Run tests and document unverified deployment checks honestly.
- Target Frappe 15, 16, and latest through explicit compatibility checks.

## Release notes

- Always update the separate `RELEASE_NOTES.md` with every implemented feature,
  change, and fix in the same change set, including documentation and tooling changes.
- Group entries under Added, Changed, and Fixed as applicable. Include validation
  results, prerequisites, migration steps, and known limitations when relevant.
- Keep work that has not been released under Unreleased. When a release is made,
  record its actual version and release date; preserve earlier release history.
- Describe delivered behavior accurately. Do not present planned features or
  unverified compatibility as completed work.
