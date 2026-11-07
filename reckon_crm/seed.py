"""Tenant seed for Reckon CRM: company roles, permissions, and assignment of existing users.

Runs once per tenant Company. Adds no business data.
"""

from __future__ import annotations

import frappe

from reckon_crm.saas_constants import TENANT_OWNED_DOCTYPES, tenant_role

GRANTS = {
    "Admin": {"read": 1, "write": 1, "create": 1, "delete": 1},
    "User": {"read": 1, "write": 1, "create": 1},
}


def ensure_company_roles(company: str) -> dict:
    roles = {}
    for kind, flags in GRANTS.items():
        role = tenant_role(kind, company)
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
        for doctype in TENANT_OWNED_DOCTYPES:
            if not frappe.db.exists("DocType", doctype):
                continue
            if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
                continue
            frappe.get_doc({
                "doctype": "Custom DocPerm", "parent": doctype, "parenttype": "DocType",
                "parentfield": "permissions", "role": role, "permlevel": 0,
                **{k: flags.get(k, 0) for k in ("read", "write", "create", "delete")},
            }).insert(ignore_permissions=True)
        roles[kind] = role
    return roles


def run_crm_seed(company: str, seed_version: str) -> dict:
    from reckon_crm.access import apply_assignment

    roles = ensure_company_roles(company)
    assignees = frappe.get_all(
        "Tenant User Assignment", filters={"company": company, "active": 1},
        fields=["user", "role_profile"],
    )
    for row in assignees:
        apply_assignment(row.user, company, row.role_profile)
    frappe.clear_cache()
    return {"company": company, "seed_version": seed_version, "roles": list(roles.values()),
            "assigned": sorted({r.user for r in assignees})}
