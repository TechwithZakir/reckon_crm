"""Tenant seed for Reckon CRM: company roles and assignment of existing users.

Runs once per tenant Company. Adds no business data. Roles and team access are
created by the platform from the module definition.
"""

from __future__ import annotations

import frappe

from reckon_crm.access import ensure_company_roles, reconcile_user
from reckon_crm.defaults import TERRITORIES


def ensure_shared_defaults() -> dict:
    """Shared starter masters (no Company field): created once, used by every tenant."""
    created = 0
    for name in TERRITORIES:
        if not frappe.db.exists("CRM Territory", name):
            frappe.get_doc({"doctype": "CRM Territory", "territory_name": name}).insert(ignore_permissions=True)
            created += 1
    return {"territories_created": created}


def run_crm_seed(company: str, seed_version: str) -> dict:
    shared = ensure_shared_defaults()
    roles = ensure_company_roles(company)
    assignees = frappe.get_all(
        "Tenant User Assignment", filters={"company": company, "active": 1}, fields=["user"],
    )
    for user in sorted({row.user for row in assignees}):
        reconcile_user(user)
    frappe.clear_cache()
    return {"company": company, "seed_version": seed_version, "roles": list(roles.values()),
            "assigned": sorted({r.user for r in assignees})}
