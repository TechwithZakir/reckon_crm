import frappe
from reckon_crm.services.settings import DEFAULTS, get_settings
from reckon_crm.utils.permissions import logged_in


def administrator_only():
    if frappe.session.user != "Administrator":
        frappe.throw("Only Administrator can manage Visit Settings.", frappe.PermissionError)


@frappe.whitelist(methods=["GET"])
def read():
    logged_in()
    administrator_only()
    return {"success": True, "data": {**get_settings(), "hrms_installed": "hrms" in frappe.get_installed_apps()}}


@frappe.whitelist(methods=["POST"])
def save(data):
    logged_in()
    administrator_only()
    data = frappe.parse_json(data) if isinstance(data, str) else data
    if not isinstance(data, dict) or set(data) != set(DEFAULTS):
        frappe.throw("Invalid settings fields.")
    doc = frappe.get_single("Reckon CRM Settings")
    doc.check_permission("write")
    doc.update(data)
    doc.save()
    return read()
