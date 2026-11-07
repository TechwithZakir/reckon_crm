"""Narrow override of CRM's lead and deal rules for tenant users.

CRM's own rules show non-Sales-Manager users only the leads and deals they own or
are assigned, and that rule is applied with AND to the platform's company rule.
Tenant users get the platform's company rule in its place. Everyone else keeps
CRM's original rules. This is a reviewed, documented exception to the no-patch
policy: it replaces four functions of the CRM app, applied when this package loads.
"""

import frappe

from reckon_saas_platform.tenant_security import (
    get_tenant_owned_query,
    has_active_tenant_assignment,
    has_tenant_owned_permission,
    user_can_bypass_tenant,
)


def _is_tenant(user):
    return bool(user) and user != "Guest" and has_active_tenant_assignment(user) and not user_can_bypass_tenant(user)


def apply():
    from crm.permissions import org_hierarchy as oh

    if getattr(oh, "_reckon_tenant_override", False):
        return

    original = {
        "lead_q": oh.get_lead_permission_query_conditions,
        "deal_q": oh.get_deal_permission_query_conditions,
        "lead_p": oh.has_lead_permission,
        "deal_p": oh.has_deal_permission,
    }

    def lead_q(user=None):
        user = user or frappe.session.user
        if _is_tenant(user):
            return get_tenant_owned_query(user=user, doctype="CRM Lead")
        return original["lead_q"](user)

    def deal_q(user=None):
        user = user or frappe.session.user
        if _is_tenant(user):
            return get_tenant_owned_query(user=user, doctype="CRM Deal")
        return original["deal_q"](user)

    def lead_p(doc, ptype, user):
        if _is_tenant(user):
            return has_tenant_owned_permission(doc, user=user, permission_type=ptype)
        return original["lead_p"](doc, ptype, user)

    def deal_p(doc, ptype, user):
        if _is_tenant(user):
            return has_tenant_owned_permission(doc, user=user, permission_type=ptype)
        return original["deal_p"](doc, ptype, user)

    oh.get_lead_permission_query_conditions = lead_q
    oh.get_deal_permission_query_conditions = deal_q
    oh.has_lead_permission = lead_p
    oh.has_deal_permission = deal_p
    oh._reckon_tenant_override = True
