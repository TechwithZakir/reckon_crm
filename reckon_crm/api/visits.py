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
    from reckon_crm.services.settings import get_settings
    return response({"user": frappe.session.user, "can_assign": is_manager(),
                     "can_manage_settings": frappe.session.user == "Administrator",
                     "settings": get_settings(),
                     "can_create": bool(frappe.has_permission("CRM Field Visit", "create"))})


@frappe.whitelist(methods=["GET"])
def assignees(reference_doctype, reference_name, search=""):
    logged_in()
    reference_doc(reference_doctype, reference_name)
    if not isinstance(search, str) or len(search) > 100:
        frappe.throw("Invalid user search.")
    if not is_manager():
        return response([{"name": frappe.session.user, "full_name": frappe.session.user}])
    # Only managers may enumerate enabled system users; return names only and
    # filter CRM role/reference access before offering assignment.
    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"},
        or_filters={"name": ["like", f"%{search}%"], "full_name": ["like", f"%{search}%"]},
        fields=["name", "full_name"], order_by="full_name asc", limit_page_length=100)
    return response([u for u in users if (u.name == "Administrator" or
        set(frappe.get_roles(u.name)).intersection({"Sales User", "Sales Manager", "System Manager"}))
        and frappe.has_permission(reference_doctype, "read", reference_name, user=u.name)])


@frappe.whitelist(methods=["POST"])
def schedule_many(data, users):
    logged_in()
    users = frappe.parse_json(users) if isinstance(users, str) else users
    if not isinstance(users, list) or not 1 <= len(users) <= 25 or any(not isinstance(u, str) or not u for u in users):
        frappe.throw("Select between 1 and 25 users.")
    users = list(dict.fromkeys(users))
    if not is_manager() and users != [frappe.session.user]:
        frappe.throw("You may only schedule visits for yourself.", frappe.PermissionError)
    data = payload(data, ("reference_doctype", "reference_name", "visit_type", "visit_purpose",
                         "planned_date", "planned_start_time", "planned_end_time", "customer_location"))
    # No commits: any failed visit/integration rolls back the whole batch.
    return response([schedule({**data, "assigned_to": user})["data"] for user in users])


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
def sync_calendar(name):
    from reckon_crm.services.settings import get_settings
    if not get_settings()["sync_calendar"]:
        frappe.throw("Calendar sync is disabled in Reckon CRM Settings.")
    doc = visit_service.locked_visit(name)
    if doc.status not in ("Planned", "Started"):
        frappe.throw("Only active visits can be added to the calendar.")
    from reckon_crm.services.calendar import sync_visit
    sync_visit(doc)
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
