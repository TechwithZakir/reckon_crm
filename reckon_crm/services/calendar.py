"""One-way visit-to-native-Event sync; invoked only by validated visit saves."""

from datetime import datetime, time, timedelta
from html import escape

import frappe
from frappe.utils import getdate, get_time

CALENDAR_TOKEN = object()


def event_values(visit, status=None):
    day = getdate(visit.planned_date)
    all_day = not visit.planned_start_time
    start = datetime.combine(day, time.min if all_day else get_time(visit.planned_start_time))
    end = (datetime.combine(day, time(23, 59, 59)) if all_day else
           datetime.combine(day, get_time(visit.planned_end_time)) if visit.planned_end_time else
           start + timedelta(hours=1))
    state = status or visit.status
    return {
        "subject": f"Field visit: {visit.reference_name}",
        "description": f"Field visit {escape(visit.name)}<br>{escape(visit.visit_purpose or '')}",
        "starts_on": start, "ends_on": end, "all_day": int(all_day),
        "event_type": "Private", "event_category": "Meeting",
        "status": "Completed" if state == "Completed" else "Cancelled" if state in ("Cancelled", "Missed") else "Open",
        "send_reminder": 0, "sync_with_google_calendar": 0,
        "reference_doctype": visit.reference_doctype, "reference_docname": visit.reference_name,
        # Administrator is a special user ID, not a valid Email field value.
        # Its own events are visible through ownership; it retains admin access.
        "event_participants": [] if visit.assigned_to == "Administrator" else [
            {"reference_doctype": "User", "reference_docname": visit.assigned_to, "email": visit.assigned_to}],
    }


def sync_visit(visit, status=None):
    # Visit insert/save has already enforced native role, reference and assignee
    # permissions. A protected persisted Link limits privileged writes to its Event.
    name = visit.get("calendar_event")
    if name:
        event = frappe.get_doc("Event", name, for_update=True)
    else:
        if not frappe.has_permission("Event", "create"):
            frappe.throw("Event creation permission is required to schedule a visit.", frappe.PermissionError)
        event = frappe.new_doc("Event")
    values = event_values(visit, status)
    required = ("subject", "starts_on", "ends_on", "all_day", "event_type", "status", "event_participants")
    if any(not event.meta.has_field(field) for field in required):
        frappe.throw("The native Event schema is incompatible with visit calendar sync. Check your Frappe version and migrations.")
    # Older supported Event schemas need not expose the CRM reference fields.
    event.update({key: value for key, value in values.items() if event.meta.has_field(key)})
    event.flags.reckon_calendar_sync = CALENDAR_TOKEN
    # Assigned users may complete a manager-created visit without native Event
    # write permission. Only the server-owned projection is written here.
    if name:
        event.save(ignore_permissions=True)
    else:
        event.insert()
        visit.db_set("calendar_event", event.name, update_modified=False)


def guard_event(event, method=None):
    if event.flags.get("reckon_calendar_sync") is CALENDAR_TOKEN:
        return
    if frappe.db.has_column("CRM Field Visit", "calendar_event") and frappe.db.exists("CRM Field Visit", {"calendar_event": event.name}):
        frappe.throw("This event is managed by a field visit. Change the visit instead.")
