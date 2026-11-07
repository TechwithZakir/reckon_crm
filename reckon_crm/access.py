"""Tenant access sync for Reckon CRM: per-tenant role, Company permission, shared-role cleanup.

Runs from the Tenant User Assignment hooks, so every assignment gets the same access.
Idempotent.
"""

from __future__ import annotations

import frappe

from reckon_crm.saas_constants import ADMIN_ROLE, ROLES, USER_ROLE, tenant_role

SHARED_ROLES = (ADMIN_ROLE, USER_ROLE)


def sync_company_permission(user: str, companies: list[str]) -> None:
    existing = frappe.get_all(
        "User Permission", filters={"user": user, "allow": "Company"}, fields=["name", "for_value"]
    )
    for row in existing:
        if row.for_value not in companies:
            frappe.delete_doc("User Permission", row.name, ignore_permissions=True, force=True)
    have = {row.for_value for row in existing if row.for_value in companies}
    for company in companies:
        if company not in have:
            frappe.get_doc({
                "doctype": "User Permission", "user": user, "allow": "Company", "for_value": company,
                "apply_to_all_doctypes": 1, "is_default": 1,
            }).insert(ignore_permissions=True)


def apply_assignment(user: str, company: str, role_profile: str | None) -> None:
    """Give the user this company's CRM role and permission, and drop the shared roles."""
    if not frappe.db.exists("User", user) or user in {"Guest", "Administrator"}:
        return
    from reckon_crm.seed import ensure_company_roles

    roles = ensure_company_roles(company)
    target = roles["Admin"] if role_profile == "Company Admin" else roles["User"]
    doc = frappe.get_doc("User", user)
    current = frappe.get_roles(user)
    if target not in current:
        doc.add_roles(target)
    for shared in SHARED_ROLES:
        if shared in current:
            doc.remove_roles(shared)
    companies = frappe.get_all("Tenant User Assignment", filters={"user": user, "active": 1}, pluck="company")
    sync_company_permission(user, sorted(set(companies)))
    frappe.clear_cache(user=user)


def sync_tenant_user_access(doc, method=None) -> None:
    """Tenant User Assignment hook. Only assignments for CRM-subscribed companies."""
    from reckon_saas_platform.saas import is_subscription_active

    if not doc.get("active") or not doc.get("user") or not doc.get("company"):
        return
    if not is_subscription_active(doc.company, "crm"):
        return
    apply_assignment(doc.user, doc.company, doc.get("role_profile"))
