"""Install without provisioning ERPNext, HRMS, or modifying CRM records."""

import frappe


def check_dependencies():
    if "crm" not in frappe.get_installed_apps():
        frappe.throw("Install Frappe CRM before installing Reckon CRM.")
    major = int(frappe.__version__.split(".")[0])
    if major < 15:
        frappe.throw("Reckon CRM requires Frappe 15 or newer.")


def clear_website_cache():
    from frappe.website.utils import clear_cache

    clear_cache()


def after_install():
    clear_website_cache()
    from reckon_crm.integrations.crm.renderer import ReckonCRMPage

    state = ReckonCRMPage("crm").asset_status()
    if not state["ready"]:
        print(f"Reckon CRM installed, but its frontend is inactive: {state['reason']}")
        print("Run: bench build --app reckon_crm")
    else:
        print("Reckon CRM frontend is ready. Open /crm/visits to see Field Visits.")
