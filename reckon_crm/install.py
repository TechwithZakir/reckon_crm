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

