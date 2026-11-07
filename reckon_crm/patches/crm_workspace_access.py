"""Let the shared Reckon CRM User role open the CRM workspace (module access for tenant users)."""

import frappe

from reckon_crm.saas_constants import USER_ROLE

WORKSPACE = "CRM"


def execute():
    if not frappe.db.exists("Workspace", WORKSPACE):
        return
    if not frappe.db.exists("Role", USER_ROLE):
        frappe.get_doc({"doctype": "Role", "role_name": USER_ROLE, "desk_access": 1}).insert(ignore_permissions=True)
    ws = frappe.get_doc("Workspace", WORKSPACE)
    if USER_ROLE in [row.role for row in ws.roles]:
        return
    ws.append("roles", {"role": USER_ROLE})
    ws.save(ignore_permissions=True)
    frappe.clear_cache()
