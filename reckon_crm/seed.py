"""Tenant seed for Reckon CRM: per-tenant roles, their CRM permissions and assignment.

Runs once per tenant Company. Roles are named per Company, so each tenant's roles
are separate. The seed adds no business data.
"""

from __future__ import annotations

import frappe

from reckon_crm.saas_constants import ADMIN_ROLE, TENANT_OWNED_DOCTYPES, USER_ROLE, tenant_role

GRANTS = {
    "Admin": {"read": 1, "write": 1, "create": 1, "delete": 1},
    "User": {"read": 1, "write": 1, "create": 1},
}


def _ensure_role(role):
    if not frappe.db.exists("Role", role):
        frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def _ensure_permissions(role, flags):
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


def _assign(company, admin_role, user_role):
    assignees = frappe.get_all(
        "Tenant User Assignment", filters={"company": company, "active": 1}, pluck="user"
    )
    for email in set(assignees):
        user = frappe.get_doc("User", email)
        user.add_roles(admin_role)
        for shared in (ADMIN_ROLE, USER_ROLE):
            if shared in frappe.get_roles(email):
                user.remove_roles(shared)
    return sorted(set(assignees))


def run_crm_seed(company: str, seed_version: str) -> dict:
    admin_role = tenant_role("Admin", company)
    user_role = tenant_role("User", company)
    _ensure_role(admin_role)
    _ensure_role(user_role)
    _ensure_permissions(admin_role, GRANTS["Admin"])
    _ensure_permissions(user_role, GRANTS["User"])
    assigned = _assign(company, admin_role, user_role)
    frappe.clear_cache()
    return {"company": company, "seed_version": seed_version, "roles": [admin_role, user_role], "assigned": assigned}
