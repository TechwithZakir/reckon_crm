"""Run only on a disposable Bench test site after migrating Reckon CRM."""

import frappe
from frappe.tests.utils import FrappeTestCase

from reckon_crm.api import visits


class TestCRMFieldVisit(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        status = frappe.db.get_value("CRM Lead Status", {}, "name")
        self.lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Reckon Visit Test", "status": status}).insert()

    def test_lifecycle_and_direct_audit_mutation(self):
        scheduled = visits.schedule({"reference_doctype": "CRM Lead", "reference_name": self.lead.name,
            "visit_purpose": "Test visit", "planned_date": frappe.utils.nowdate()})["data"]
        doc = frappe.get_doc("CRM Field Visit", scheduled["name"])
        self.assertTrue(doc.calendar_event)
        event = frappe.get_doc("Event", doc.calendar_event)
        self.assertEqual(event.event_type, "Private")
        self.assertTrue(event.all_day)
        event.subject = "Direct edit"
        with self.assertRaises(frappe.ValidationError):
            event.save()
        doc.status = "Completed"
        with self.assertRaises(frappe.ValidationError):
            doc.save()
        started = visits.check_in(scheduled["name"], 0, 0, 5)["data"]
        self.assertEqual(started["status"], "Started")
        completed = visits.check_out(scheduled["name"], "Interested")["data"]
        self.assertEqual(completed["status"], "Completed")
        self.assertEqual(frappe.db.get_value("Event", doc.calendar_event, "status"), "Completed")
        self.assertTrue(frappe.db.exists("Comment", {"reference_doctype": "CRM Lead", "reference_name": self.lead.name,
            "content": ["like", f"%{scheduled['name']}%"]}))
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            visits.check_out(scheduled["name"], "Duplicate")

    def test_reschedule_sync_and_cancel_reuse_event(self):
        scheduled = visits.schedule({"reference_doctype": "CRM Lead", "reference_name": self.lead.name,
            "visit_purpose": "Calendar test", "planned_date": frappe.utils.nowdate(),
            "planned_start_time": "09:00:00", "planned_end_time": "10:00:00"})["data"]
        doc = frappe.get_doc("CRM Field Visit", scheduled["name"])
        event_name = doc.calendar_event
        doc.planned_start_time = "11:00:00"
        doc.planned_end_time = "12:00:00"
        doc.save()
        self.assertEqual(doc.calendar_event, event_name)
        self.assertEqual(frappe.get_doc("Event", event_name).starts_on.hour, 11)
        visits.sync_calendar(doc.name)
        self.assertEqual(frappe.db.get_value("CRM Field Visit", doc.name, "calendar_event"), event_name)
        visits.cancel(doc.name)
        self.assertEqual(frappe.db.get_value("Event", event_name, "status"), "Cancelled")

    def test_guest_cannot_list_or_schedule(self):
        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                visits.list_visits()
            with self.assertRaises(frappe.PermissionError):
                visits.schedule({})
        finally:
            frappe.set_user("Administrator")
