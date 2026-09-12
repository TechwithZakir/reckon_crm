import frappe

from reckon_crm.api.visits import payload, response
from reckon_crm.utils.geo import verify_position
from reckon_crm.utils.permissions import logged_in, reference_doc


@frappe.whitelist(methods=["GET"])
def locations(reference_doctype, reference_name):
    reference_doc(reference_doctype, reference_name)
    return response(frappe.get_list("CRM Customer Location", fields=["name", "location_name", "latitude",
        "longitude", "geofence_radius", "address", "is_primary"],
        filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
        order_by="is_primary desc, location_name asc", limit_page_length=100))


@frappe.whitelist(methods=["POST"])
def create_location(data):
    logged_in()
    data = payload(data, ("reference_doctype", "reference_name", "location_name", "address", "latitude",
                         "longitude", "geofence_radius", "location_type", "is_primary"))
    doc = frappe.get_doc({"doctype": "CRM Customer Location", **data}).insert()
    return response(doc.as_dict())


@frappe.whitelist(methods=["POST"])
def preview(name, latitude=None, longitude=None, accuracy=None):
    logged_in()
    doc = frappe.get_doc("CRM Field Visit", name)
    doc.check_permission("read")
    reference_doc(doc.reference_doctype, doc.reference_name)
    location = None
    if doc.customer_location:
        location_doc = frappe.get_doc("CRM Customer Location", doc.customer_location)
        location_doc.check_permission("read")
        if (location_doc.reference_doctype, location_doc.reference_name) != (doc.reference_doctype, doc.reference_name):
            frappe.throw("The customer location no longer matches this visit.")
        location = location_doc.as_dict()
    try:
        result = verify_position(latitude, longitude, accuracy, location)
    except ValueError as error:
        frappe.throw(str(error))
    result["allowed_radius"] = location["geofence_radius"] if location else None
    return response(result)
