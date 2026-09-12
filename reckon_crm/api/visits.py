"""Phase 1 API. Normal Frappe document permissions apply to all reads and writes."""

import frappe

from reckon_crm.services import visit_service
from reckon_crm.utils.permissions import REFERENCES, is_manager, logged_in, reference_doc


def response(data):
    return {"success": True, "data": data, "message": None}


def payload(value, allowed):
    value = frappe.parse_json(value) if isinstance(value, str) else value
    if not isinstance(value, dict) or set(value) - set(allowed):
        frappe.throw("Invalid request fields.")
    return value


@frappe.whitelist(methods=["GET"])
def context():
    logged_in()
    return response({"user": frappe.session.user, "can_assign": is_manager(),
                     "can_create": bool(frappe.has_permission("CRM Field Visit", "create"))})


@frappe.whitelist(methods=["GET"])
def references(doctype, search=""):
    logged_in()
    if doctype not in REFERENCES:
        frappe.throw("Unsupported CRM record type.")
    if not isinstance(search, str) or len(search) > 100:
        frappe.throw("Search is too long.")
    title = frappe.get_meta(doctype).title_field or "name"
    fields = ["name"] if title == "name" else ["name", title]
    rows = frappe.get_list(doctype, fields=fields, filters={"name": ["like", f"%{search}%"]}, limit_page_length=30)
    return response([{"name": row.name, "label": row.get(title) or row.name} for row in rows])


@frappe.whitelist(methods=["GET"])
def list_visits(reference_doctype=None, reference_name=None, status=None):
    logged_in()
    filters = {}
    if reference_doctype or reference_name:
        reference_doc(reference_doctype, reference_name)
        filters.update(reference_doctype=reference_doctype, reference_name=reference_name)
    if status:
        if status not in ("Planned", "Started", "Completed", "Cancelled", "Missed"):
            frappe.throw("Invalid visit status.")
        filters["status"] = status
    rows = frappe.get_list("CRM Field Visit", fields=["name", "reference_doctype", "reference_name",
        "planned_date", "planned_start_time", "assigned_to", "status", "visit_purpose", "geo_status"],
        filters=filters, order_by="planned_date desc, creation desc", limit_page_length=100)
    return response(rows)


@frappe.whitelist(methods=["GET"])
def get_visit(name):
    logged_in()
    doc = frappe.get_doc("CRM Field Visit", name)
    doc.check_permission("read")
    reference_doc(doc.reference_doctype, doc.reference_name)
    return response(doc.as_dict())


@frappe.whitelist(methods=["POST"])
def schedule(data):
    logged_in()
    data = payload(data, ("reference_doctype", "reference_name", "visit_type", "visit_purpose",
                         "planned_date", "planned_start_time", "planned_end_time", "assigned_to", "customer_location"))
    doc = frappe.get_doc({"doctype": "CRM Field Visit", **data, "status": "Planned"})
    doc.assigned_to = doc.assigned_to or frappe.session.user
    doc.insert()
    return response(doc.as_dict())


@frappe.whitelist(methods=["POST"])
def check_in(name, latitude=None, longitude=None, accuracy=None):
    return response(visit_service.check_in(name, latitude, longitude, accuracy).as_dict())


@frappe.whitelist(methods=["POST"])
def check_out(name, outcome, notes="", next_followup_date=None, latitude=None, longitude=None, accuracy=None):
    return response(visit_service.check_out(name, outcome, notes, next_followup_date, latitude, longitude, accuracy).as_dict())


@frappe.whitelist(methods=["POST"])
def cancel(name):
    return response(visit_service.cancel(name).as_dict())


@frappe.whitelist(methods=["POST"])
def attach_file(name, fieldname, file_url):
    if fieldname not in ("attachment", "photo"):
        frappe.throw("Invalid attachment field.")
    doc = visit_service.locked_visit(name)
    if doc.status not in ("Planned", "Started"):
        frappe.throw("Attach files before completing the visit.")
    files = frappe.get_list("File", filters={"file_url": file_url, "attached_to_doctype": "CRM Field Visit",
        "attached_to_name": name, "is_private": 1}, fields=["name"], limit_page_length=1)
    if not files:
        frappe.throw("Upload a private file attached to this visit first.", frappe.PermissionError)
    frappe.get_doc("File", files[0].name).check_permission("read")
    doc.set(fieldname, file_url)
    doc.save()
    return response(doc.as_dict())
