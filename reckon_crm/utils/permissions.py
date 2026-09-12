"""Use native CRM permissions as the reference-record access boundary."""

import frappe
from reckon_crm.utils.lifecycle import TRANSITION_TOKEN

REFERENCES = ("CRM Lead", "CRM Deal", "CRM Organization")
MANAGERS = {"Sales Manager", "System Manager"}


def logged_in():
    if frappe.session.user == "Guest":
        frappe.throw("Please sign in.", frappe.PermissionError)


def is_manager(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or bool(MANAGERS.intersection(frappe.get_roles(user)))


def reference_doc(doctype, name, permission="read"):
    logged_in()
    if doctype not in REFERENCES or not isinstance(name, str) or not name.strip():
        frappe.throw("Select a CRM Lead, CRM Deal, or CRM Organization.")
    doc = frappe.get_doc(doctype, name)
    doc.check_permission(permission)
    return doc


def document_permission(doc, user=None, ptype=None):
    user = user or frappe.session.user
    if user == "Guest":
        return False
    if not doc.reference_name:
        return None  # Frappe's role permissions still decide creation.
    if doc.reference_doctype not in REFERENCES:
        return False
    if not frappe.has_permission(doc.reference_doctype, "read", doc.reference_name, user=user):
        return False
    if doc.doctype == "CRM Field Visit" and not is_manager(user):
        if doc.assigned_to != user:
            return False
    if ptype in ("write", "delete") and doc.doctype == "CRM Field Visit":
        if doc.status in ("Completed", "Cancelled", "Missed") and doc.flags.get("reckon_transition") is not TRANSITION_TOKEN:
            return False
    return None  # Never grant rights beyond the DocType's role permissions.


def query_conditions(user=None, doctype="CRM Field Visit"):
    """Native Desk lists/exports must respect reference permissions too.

    Frappe exposes SQL conditions for this hook. Identifiers are fixed and every
    value is escaped by the database driver; permitted names come from get_list.
    """
    user = user or frappe.session.user
    if user == "Guest":
        return "1=0"
    clauses = []
    table = f"`tab{doctype}`"
    for reference in REFERENCES:
        if not frappe.has_permission(reference, "read", user=user):
            continue
        names = frappe.get_list(reference, pluck="name", limit_page_length=0, user=user)
        if names:
            values = ",".join(frappe.db.escape(name) for name in names)
            clauses.append(f"({table}.reference_doctype={frappe.db.escape(reference)} AND {table}.reference_name IN ({values}))")
    condition = "(" + " OR ".join(clauses) + ")" if clauses else "1=0"
    if doctype == "CRM Field Visit" and not is_manager(user):
        condition += f" AND {table}.assigned_to={frappe.db.escape(user)}"
    return condition


def location_query_conditions(user=None):
    return query_conditions(user, "CRM Customer Location")
