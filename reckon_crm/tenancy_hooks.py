"""doc_events wrappers for the platform's tenant functions (see reckon_hrms.tenancy_hooks)."""

import frappe

from reckon_saas_platform.tenant_security import (
    bind_doc_to_tenant,
    validate_tenant_company_immutable,
    validate_tenant_owned_doc,
)


def bind_company(doc, method=None, *args, **kwargs):
    bind_doc_to_tenant(doc, user=frappe.session.user)


def validate_company_immutable(doc, method=None, *args, **kwargs):
    validate_tenant_company_immutable(doc)


def validate_owned(doc, method=None, *args, **kwargs):
    validate_tenant_owned_doc(doc, user=frappe.session.user)


# ---------- Tasks and notes: scoped by who made them ----------
# CRM Task and FCRM Note carry no Company of their own; they belong to the company of the user who created them.

_WRITE_RIGHTS = {"create", "write", "delete", "submit", "cancel", "amend"}


def _own_company_or_none(user: str | None):
    from reckon_saas_platform.tenant_security import tenant_company_or_none

    return tenant_company_or_none(user or frappe.session.user)


def owner_company_query(user=None, doctype=None):
    """Only rows made by someone in the caller's company; staff of the platform see everything."""
    from reckon_saas_platform.tenant_security import user_can_bypass_tenant

    user = user or frappe.session.user
    if user_can_bypass_tenant(user):
        return ""
    company = _own_company_or_none(user)
    if not company:
        return "1=0"
    return (
        f"`tab{doctype or 'CRM Task'}`.`owner` in (select `user` from `tabTenant User Assignment` "
        f"where `company` = {frappe.db.escape(company)} and `active` = 1)"
    )


def owner_company_permission(doc, user=None, permission_type=None, ptype=None, **_ignored):
    from reckon_saas_platform.tenant_security import user_can_bypass_tenant

    user = user or frappe.session.user
    if user_can_bypass_tenant(user):
        return True
    company = _own_company_or_none(user)
    if not company:
        return False
    if (permission_type or ptype) == "create" or doc.is_new():
        return True  # a new row is made by the caller, so it is the caller's company's
    return bool(frappe.db.exists("Tenant User Assignment", {"user": doc.owner, "company": company, "active": 1}))
