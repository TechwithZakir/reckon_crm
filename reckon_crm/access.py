"""Tenant access for Reckon CRM: per-company roles and Company permissions, reconciled per user.

A user's Reckon CRM roles always match their active assignments in CRM-subscribed
companies. Adding, changing or deactivating an assignment reconciles the whole set.
"""

from __future__ import annotations

import frappe

from reckon_crm.saas_constants import ADMIN_ROLE, USER_ROLE

SHARED_ROLES = (ADMIN_ROLE, USER_ROLE)
MODULE_ROLE_PREFIX = "Reckon CRM "


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


def reconcile_user(user: str) -> None:
    """Make the user's Reckon CRM roles and Company permissions match their active assignments.

    Role changes run as Administrator even when a company admin triggered them; the
    caller's session is restored afterwards.
    """
    caller = frappe.session.user
    frappe.set_user("Administrator")
    try:
        _reconcile(user)
    finally:
        frappe.set_user(caller)


def _reconcile(user: str) -> None:
    from reckon_crm.seed import ensure_company_roles
    from reckon_saas_platform.saas import is_subscription_active

    if not user or user in {"Guest", "Administrator"} or not frappe.db.exists("User", user):
        return
    rows = frappe.get_all(
        "Tenant User Assignment", filters={"user": user, "active": 1}, fields=["company", "role_profile"]
    )
    desired, companies = set(), []
    for row in rows:
        if not is_subscription_active(row.company, "crm"):
            continue
        roles = ensure_company_roles(row.company)
        desired.add(roles["Admin"] if row.role_profile == "Company Admin" else roles["User"])
        companies.append(row.company)

    module_roles = {
        r for r in frappe.get_all("Role", filters={"name": ["like", MODULE_ROLE_PREFIX + "%"]}, pluck="name")
        if " - " in r
    }
    doc = frappe.get_doc("User", user)
    current = set(frappe.get_roles(user))
    for role in sorted(desired - current):
        doc.add_roles(role)
    for role in sorted(((module_roles | set(SHARED_ROLES)) & current) - desired):
        doc.remove_roles(role)
    sync_company_permission(user, sorted(set(companies)))
    frappe.clear_cache(user=user)


def sync_tenant_user_access(doc, method=None) -> None:
    """Tenant User Assignment hook: reconcile the user, including when an assignment is deactivated."""
    if doc.get("user"):
        reconcile_user(doc.user)
