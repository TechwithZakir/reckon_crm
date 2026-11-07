"""Tenant seed for Reckon CRM: company roles and assignment of existing users.

Runs once per tenant Company. Adds no business data. Roles and team access are
created by the platform from the module definition.
"""

from __future__ import annotations

import frappe

from reckon_crm.access import ensure_company_roles, reconcile_user


def run_crm_seed(company: str, seed_version: str) -> dict:
    roles = ensure_company_roles(company)
    assignees = frappe.get_all(
        "Tenant User Assignment", filters={"company": company, "active": 1}, fields=["user"],
    )
    for user in sorted({row.user for row in assignees}):
        reconcile_user(user)
    frappe.clear_cache()
    return {"company": company, "seed_version": seed_version, "roles": list(roles.values()),
            "assigned": sorted({r.user for r in assignees})}
