import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_time, nowdate

from reckon_crm.utils.permissions import is_manager, reference_doc
from reckon_crm.utils.lifecycle import TRANSITION_TOKEN

AUDIT_FIELDS = (
    "status", "checkin_time", "checkin_latitude", "checkin_longitude", "checkin_accuracy",
    "checkin_by", "checkout_time", "checkout_latitude", "checkout_longitude", "checkout_accuracy",
    "checkout_by", "distance_from_customer", "geo_status", "allowed_radius", "duration_minutes",
    "outcome", "notes", "next_followup_date", "checkout_geo_status", "checkout_distance",
    "location_latitude", "location_longitude",
)


class CRMFieldVisit(Document):
    def validate(self):
        reference_doc(self.reference_doctype, self.reference_name)
        previous = self.get_doc_before_save()
        if (self.is_new() and self.get("calendar_event")) or (previous and self.get("calendar_event") != previous.get("calendar_event")):
            frappe.throw("Calendar event links are managed by the visit.")
        for field in ("crm_task", "employee_checkin", "employee_checkout"):
            if (self.is_new() and self.get(field)) or (previous and self.get(field) != previous.get(field)):
                frappe.throw("Integration links are managed by the visit.")
        for fieldname in ("attachment", "photo"):
            file_url = self.get(fieldname)
            if file_url and (not previous or file_url != previous.get(fieldname)):
                if not isinstance(file_url, str) or not file_url.startswith("/private/files/"):
                    frappe.throw("Visit attachments must be private files.")
                files = frappe.get_list("File", filters={"file_url": file_url,
                    "attached_to_doctype": "CRM Field Visit", "attached_to_name": self.name,
                    "is_private": 1}, fields=["name"], limit_page_length=1)
                if self.is_new() or not files:
                    frappe.throw("Upload a private file attached to this saved visit first.", frappe.PermissionError)
                frappe.get_doc("File", files[0].name).check_permission("read")
        transition = self.flags.get("reckon_transition") is TRANSITION_TOKEN
        if previous and previous.status in ("Completed", "Cancelled", "Missed"):
            frappe.throw("Closed visits cannot be changed.")
        if self.is_new():
            if self.status != "Planned" or any(self.get(field) for field in AUDIT_FIELDS if field not in ("status", "geo_status")):
                frappe.throw("Create visits in Planned status without audit data.")
            self.geo_status = "Not Checked"
        elif not transition:
            if any(self.get(field) != previous.get(field) for field in AUDIT_FIELDS):
                frappe.throw("Use the visit check-in/check-out actions to change audit fields.")
        if previous:
            if (self.reference_doctype, self.reference_name) != (previous.reference_doctype, previous.reference_name):
                frappe.throw("A visit's CRM reference cannot be changed.")
            if previous.status == "Started" and any(self.get(field) != previous.get(field) for field in (
                "assigned_to", "customer_location", "planned_date", "planned_start_time", "planned_end_time",
                "visit_type", "visit_purpose",
            )):
                frappe.throw("An active visit's schedule, location, and assignee cannot be changed.")
        if not is_manager() and self.assigned_to != frappe.session.user:
            frappe.throw("You may only schedule visits for yourself.", frappe.PermissionError)
        if not frappe.db.get_value("User", self.assigned_to, "enabled"):
            frappe.throw("Choose an enabled user.")
        if not set(frappe.get_roles(self.assigned_to)).intersection({"Sales User", "Sales Manager", "System Manager"}) and self.assigned_to != "Administrator":
            frappe.throw("The assignee needs a CRM sales role.")
        if not frappe.has_permission(self.reference_doctype, "read", self.reference_name, user=self.assigned_to):
            frappe.throw("The assignee cannot access this CRM record.")
        if self.customer_location and (self.is_new() or not transition):
            location = frappe.get_doc("CRM Customer Location", self.customer_location)
            location.check_permission("read")
            if (location.reference_doctype, location.reference_name) != (self.reference_doctype, self.reference_name):
                frappe.throw("The customer location must belong to the visit's CRM record.")
        if self.planned_start_time and self.planned_end_time:
            if get_time(self.planned_end_time) <= get_time(self.planned_start_time):
                frappe.throw("Planned end time must be later than start time.")
        if self.planned_end_time and not self.planned_start_time:
            frappe.throw("Enter a start time when specifying an end time.")
        if self.next_followup_date and getdate(self.next_followup_date) < getdate(nowdate()):
            frappe.throw("Next follow-up cannot be in the past.")

    def on_update(self):
        from reckon_crm.services.sync import sync_visit
        sync_visit(self)

    def on_trash(self):
        if self.status != "Planned":
            frappe.throw("Only planned visits may be deleted.")
        if self.get("calendar_event") or self.get("crm_task"):
            from reckon_crm.services.sync import sync_visit
            sync_visit(self, status="Cancelled")
