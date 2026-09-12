"""Site diagnostics for `bench --site SITE execute reckon_crm.diagnostics.status`.

Intentionally not whitelisted: this is an administrator's Bench command, not a
public HTTP API. It does not write records or expose credentials.
"""

import frappe

from reckon_crm.integrations.crm.renderer import ReckonCRMPage


def status():
    apps = frappe.get_installed_apps()
    if "crm" not in apps:
        return {"ready": False, "reason": "Install Frappe CRM on this site first."}
    if "reckon_crm" not in apps:
        return {"ready": False, "reason": "Reckon CRM is not installed on this site."}
    hook = "reckon_crm.integrations.crm.renderer.ReckonCRMPage"
    if hook not in (frappe.get_hooks("page_renderer") or []):
        return {"ready": False, "reason": "Reckon renderer hook is missing. Clear the site cache and restart Bench."}
    result = ReckonCRMPage("crm").asset_status()
    assets_ready = result["ready"]
    result["schema_ready"] = all(frappe.db.exists("DocType", name) for name in ("CRM Field Visit", "CRM Customer Location"))
    result["schema_ready"] = result["schema_ready"] and frappe.db.has_column("CRM Field Visit", "calendar_event")
    if not result["schema_ready"]:
        result["migrate_command"] = "bench --site YOUR_SITE migrate"
        if result["ready"]:
            result.update(ready=False, reason="Field visit DocTypes or calendar fields are missing. Migrate this site before using visits.")
    result["url"] = "/crm/visits"
    result["scope"] = "Phase 1: schedule visits, customer locations, check-in/check-out, and visit history. Run site migration before using the new APIs."
    if frappe.conf.get("reckon_crm_disabled"):
        result["enable_command"] = "bench --site YOUR_SITE set-config reckon_crm_disabled 0"
    elif not assets_ready:
        result["build_command"] = "bench build --app reckon_crm"
    return result
