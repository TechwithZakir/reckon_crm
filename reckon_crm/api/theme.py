import frappe
from reckon_crm.utils.permissions import logged_in


@frappe.whitelist(methods=["GET"])
def dock_config():
    """Public Aura settings for the CRM's tools dock. Never returns secrets."""
    logged_in()
    try:
        from reckon_aura_theme.api import get_public_config
    except ImportError:
        # reckon_aura_theme is not installed on this site: no dock, no theme.
        return {"enabled": 0}
    return get_public_config()
