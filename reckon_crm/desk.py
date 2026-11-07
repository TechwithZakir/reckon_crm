"""Desk entry points for Reckon CRM."""

from __future__ import annotations

import frappe

from reckon_crm.saas_constants import ADMIN_ROLE, ROLES, USER_ROLE


def can_see_app() -> bool:
    """The Reckon CRM tile shows for Administrators and for users with a CRM role."""
    user = frappe.session.user
    if user == "Guest":
        return False
    if user == "Administrator":
        return True
    roles = set(frappe.get_roles(user))
    return bool(roles & (set(ROLES) | {ADMIN_ROLE, USER_ROLE})) or any(
        role.startswith("Reckon CRM ") and " - " in role for role in roles
    )
