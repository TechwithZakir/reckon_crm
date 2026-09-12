"""Site-level switches; no optional app imports."""
import frappe

DEFAULTS = {"sync_calendar": 1, "sync_tasks": 0, "sync_employee_checkin": 0, "skip_auto_attendance": 1}


def get_settings():
    if not frappe.db.exists("DocType", "Reckon CRM Settings"):
        return dict(DEFAULTS)
    doc = frappe.get_single("Reckon CRM Settings")
    return {key: int(doc.get(key) if doc.get(key) is not None else default) for key, default in DEFAULTS.items()}


def validate_settings(doc):
    for field in DEFAULTS:
        if doc.get(field) not in (0, 1, False, True, "0", "1"):
            frappe.throw("Settings must be enabled or disabled.")
    if int(doc.sync_employee_checkin):
        if "hrms" not in frappe.get_installed_apps() or not frappe.db.exists("DocType", "Employee Checkin"):
            frappe.throw("Install HRMS before enabling Employee Checkin sync.")
