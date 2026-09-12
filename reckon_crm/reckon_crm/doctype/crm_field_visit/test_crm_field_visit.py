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
        doc.status = "Completed"
        with self.assertRaises(frappe.ValidationError):
            doc.save()
        started = visits.check_in(scheduled["name"], 0, 0, 5)["data"]
        self.assertEqual(started["status"], "Started")
        completed = visits.check_out(scheduled["name"], "Interested")["data"]
        self.assertEqual(completed["status"], "Completed")
        self.assertTrue(frappe.db.exists("Comment", {"reference_doctype": "CRM Lead", "reference_name": self.lead.name,
            "content": ["like", f"%{scheduled['name']}%"]}))
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            visits.check_out(scheduled["name"], "Duplicate")

    def test_guest_cannot_list_or_schedule(self):
        frappe.set_user("Guest")
        try:
            with self.assertRaises(frappe.PermissionError):
                visits.list_visits()
            with self.assertRaises(frappe.PermissionError):
                visits.schedule({})
        finally:
            frappe.set_user("Administrator")
