"""Reckon CRM registration in reckon_saas_platform (``reckon_saas_modules`` hook)."""

from __future__ import annotations

from reckon_crm.saas_constants import (
    ADMIN_ROLE,
    DESK_DOCTYPES,
    DESK_GUARD,
    DESK_WORKSPACES,
    HOME_ROUTE,
    MODULE_FEATURES,
    MODULE_KEY,
    MODULE_LABEL,
    ROLES,
    TENANT_OWNED_DOCTYPES,
    USER_ROLE,
    WORKSPACE,
)


def get_module_definition() -> dict:
    return {
        "key": MODULE_KEY,
        "label": MODULE_LABEL,
        "description": "Leads, deals and organizations for sales teams, one Company per tenant.",
        "workspace": WORKSPACE,
        "home_route": HOME_ROUTE,
        "admin_role": ADMIN_ROLE,
        "roles": list(ROLES),
        "seed_handler": "reckon_crm.seed.run_crm_seed",
        "subscription_features": list(MODULE_FEATURES),
        "desk_guard": DESK_GUARD,
        "desk_doctypes": list(DESK_DOCTYPES),
        "desk_workspaces": list(DESK_WORKSPACES),
        # The platform creates per-company roles and reconciles team access for these.
        "tenant_role_prefix": "Reckon CRM",
        "tenant_doctypes": list(TENANT_OWNED_DOCTYPES),
        # Workspace and app access for CRM users. It grants no data rights; those are per company.
        "tenant_shared_role": USER_ROLE,
    }
