"""Reckon CRM registration in reckon_saas_platform (``reckon_saas_modules`` hook)."""

from __future__ import annotations

from reckon_crm.saas_constants import (
    ADMIN_ROLE,
    HOME_ROUTE,
    MODULE_FEATURES,
    MODULE_KEY,
    MODULE_LABEL,
    ROLES,
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
    }
