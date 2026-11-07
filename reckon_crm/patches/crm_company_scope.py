"""Add the Company field to CRM Lead, Deal and Organization, and create the CRM tenant roles."""

import frappe

from reckon_crm.saas_constants import ADMIN_ROLE, ROLES, TENANT_OWNED_DOCTYPES, USER_ROLE

GRANTS = {
    ADMIN_ROLE: {"read": 1, "write": 1, "create": 1, "delete": 1},
    USER_ROLE: {"read": 1, "write": 1, "create": 1},
}


def execute():
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
                ignore_permissions=True
            )
    for doctype in TENANT_OWNED_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            continue
        if not frappe.db.exists("Custom Field", f"{doctype}-company"):
            frappe.get_doc(
                {
                    "doctype": "Custom Field",
                    "dt": doctype,
                    "fieldname": "company",
                    "label": "Company",
                    "fieldtype": "Link",
                    "options": "Company",
                    "read_only": 1,
                    "reqd": 0,
                }
            ).insert(ignore_permissions=True)
        for role, flags in GRANTS.items():
            if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
                continue
            frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": doctype,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role,
                    "permlevel": 0,
                    **{k: flags.get(k, 0) for k in ("read", "write", "create", "delete")},
                }
            ).insert(ignore_permissions=True)
    frappe.clear_cache()
