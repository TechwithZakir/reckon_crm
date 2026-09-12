from html import escape

import frappe
from frappe.utils import get_datetime, now_datetime

from reckon_crm.utils.geo import coordinates, finite_number, verify_position
from reckon_crm.utils.permissions import logged_in, reference_doc
from reckon_crm.utils.lifecycle import TRANSITION_TOKEN


def locked_visit(name):
    logged_in()
    doc = frappe.get_doc("CRM Field Visit", name, for_update=True)
    doc.check_permission("write")
    reference_doc(doc.reference_doctype, doc.reference_name)
    return doc


def sample(latitude, longitude, accuracy):
    if latitude is None and longitude is None and accuracy is None:
        return None, None, None
    lat, lon = coordinates(latitude, longitude)
    return lat, lon, finite_number(accuracy, "GPS accuracy", 0, 100000)


def check_in(name, latitude=None, longitude=None, accuracy=None):
    doc = locked_visit(name)
    if doc.assigned_to != frappe.session.user:
        frappe.throw("Only the assigned user can check in.", frappe.PermissionError)
    if doc.status != "Planned":
        frappe.throw("Only a planned visit can be checked in.")
    location = None
    if doc.customer_location:
        location_doc = frappe.get_doc("CRM Customer Location", doc.customer_location)
        location_doc.check_permission("read")
        if (location_doc.reference_doctype, location_doc.reference_name) != (doc.reference_doctype, doc.reference_name):
            frappe.throw("Customer location no longer belongs to this CRM record.")
        location = location_doc.as_dict()
        doc.location_latitude = location["latitude"]
        doc.location_longitude = location["longitude"]
        doc.allowed_radius = location["geofence_radius"]
    try:
        lat, lon, precision = sample(latitude, longitude, accuracy)
        result = verify_position(lat, lon, precision, location)
    except ValueError as error:
        frappe.throw(str(error))
    doc.update(result)
    doc.update({"status": "Started", "checkin_time": now_datetime(), "checkin_latitude": lat,
                "checkin_longitude": lon, "checkin_accuracy": precision, "checkin_by": frappe.session.user})
    doc.flags.reckon_transition = TRANSITION_TOKEN
    doc.save()
    return doc


def check_out(name, outcome, notes="", next_followup_date=None, latitude=None, longitude=None, accuracy=None):
    doc = locked_visit(name)
    if doc.assigned_to != frappe.session.user:
        frappe.throw("Only the assigned user can check out.", frappe.PermissionError)
    if doc.status != "Started":
        frappe.throw("Only a started visit can be checked out.")
    if not isinstance(outcome, str) or not outcome.strip() or len(outcome) > 140:
        frappe.throw("Enter an outcome of at most 140 characters.")
    if not isinstance(notes, str) or len(notes) > 10000:
        frappe.throw("Visit notes must be at most 10,000 characters.")
    location = None
    if doc.customer_location and doc.allowed_radius:
        location = {"latitude": doc.location_latitude, "longitude": doc.location_longitude,
                    "geofence_radius": doc.allowed_radius}
    try:
        lat, lon, precision = sample(latitude, longitude, accuracy)
        result = verify_position(lat, lon, precision, location)
    except ValueError as error:
        frappe.throw(str(error))
    completed_at = now_datetime()
    duration = (completed_at - get_datetime(doc.checkin_time)).total_seconds() / 60
    if duration < 0:
        frappe.throw("Check-out time cannot precede check-in time.")
    doc.update({"status": "Completed", "checkout_time": completed_at, "checkout_latitude": lat,
                "checkout_longitude": lon, "checkout_accuracy": precision, "checkout_by": frappe.session.user,
                "checkout_geo_status": result["geo_status"], "checkout_distance": result["distance_from_customer"],
                "duration_minutes": round(duration, 2), "outcome": outcome.strip(), "notes": notes,
                "next_followup_date": next_followup_date or None})
    doc.flags.reckon_transition = TRANSITION_TOKEN
    doc.save()
    # Same database transaction as completion; a failure rolls back both writes.
    reference = reference_doc(doc.reference_doctype, doc.reference_name)
    summary = f"Field Visit Completed: {escape(doc.name)}<br>Duration: {doc.duration_minutes} minutes<br>Outcome: {escape(doc.outcome)}"
    if doc.next_followup_date:
        summary += f"<br>Next follow-up: {escape(str(doc.next_followup_date))}"
    reference.add_comment("Comment", summary)
    return doc


def cancel(name):
    doc = locked_visit(name)
    if doc.status != "Planned":
        frappe.throw("Only a planned visit can be cancelled.")
    doc.status = "Cancelled"
    doc.flags.reckon_transition = TRANSITION_TOKEN
    doc.save()
    return doc
