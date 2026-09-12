import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from datetime import date, time

from test_visit_service import Record


class DocumentDouble(Record):
    def is_new(self):
        return self.get("new", False)

    def get_doc_before_save(self):
        return self.get("previous")


class VisitPermissionTests(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType("frappe")
        frappe.session = Record(user="sales@example.invalid")
        frappe.PermissionError = PermissionError
        def throw(message, exception=ValueError):
            raise exception(message)
        frappe.throw = throw
        frappe.get_roles = Mock(return_value=["Sales User"])
        frappe.has_permission = Mock(return_value=True)
        frappe.get_doc = Mock(return_value=Record())
        frappe.db = Record(get_value=Mock(return_value=1), escape=lambda value: "'" + value.replace("'", "''") + "'")
        frappe.get_list = Mock(return_value=["PERMITTED-'1"])
        model = types.ModuleType("frappe.model")
        document = types.ModuleType("frappe.model.document")
        document.Document = DocumentDouble
        utils = types.ModuleType("frappe.utils")
        utils.getdate = lambda value: date.fromisoformat(str(value))
        utils.get_time = lambda value: time.fromisoformat(str(value))
        utils.nowdate = lambda: "2026-09-11"
        modules = patch.dict(sys.modules, {"frappe": frappe, "frappe.model": model,
                                          "frappe.model.document": document, "frappe.utils": utils})
        modules.start(); self.addCleanup(modules.stop)
        self.permissions = importlib.reload(importlib.import_module("reckon_crm.utils.permissions"))
        controller = importlib.reload(importlib.import_module("reckon_crm.reckon_crm.doctype.crm_field_visit.crm_field_visit"))
        self.controller = controller.CRMFieldVisit
        self.frappe = frappe

    def visit(self, status="Planned"):
        return self.controller(doctype="CRM Field Visit", reference_doctype="CRM Lead", reference_name="LEAD-1",
                               assigned_to=self.frappe.session.user, status=status, flags=Record())

    def test_assignment_and_parent_permission_restrict_reads(self):
        doc = self.visit()
        self.assertIsNone(self.permissions.document_permission(doc, ptype="read"))
        doc.assigned_to = "other@example.invalid"
        self.assertFalse(self.permissions.document_permission(doc, ptype="read"))
        self.frappe.get_roles.return_value = ["Sales Manager"]
        self.assertIsNone(self.permissions.document_permission(doc, ptype="read"))
        self.frappe.has_permission.return_value = False
        self.assertFalse(self.permissions.document_permission(doc, ptype="read"))

    def test_direct_attachment_fields_reject_public_or_unattached_files(self):
        doc = self.visit()
        for value in ("https://example.invalid/file", "javascript:alert(1)", "/files/public.pdf"):
            doc.attachment = value
            with self.assertRaisesRegex(ValueError, "private files"):
                doc.validate()
        doc.attachment = "/private/files/test.pdf"
        self.frappe.get_list.return_value = []
        with self.assertRaisesRegex(PermissionError, "saved visit"):
            doc.validate()

    def test_closed_visit_write_denied_even_to_manager(self):
        self.frappe.get_roles.return_value = ["Sales Manager"]
        self.assertFalse(self.permissions.document_permission(self.visit("Completed"), ptype="write"))

    def test_json_flag_cannot_forge_audit_transition(self):
        doc = self.visit("Completed")
        doc.previous = self.visit("Started")
        doc.flags.reckon_transition = True
        with self.assertRaisesRegex(ValueError, "audit fields"):
            doc.validate()

    def test_completed_visits_immutable_and_new_visits_cannot_be_started(self):
        doc = self.visit("Completed")
        doc.previous = self.visit("Completed")
        with self.assertRaisesRegex(ValueError, "Closed visits"):
            doc.validate()
        doc = self.visit("Started")
        doc.new = True
        with self.assertRaisesRegex(ValueError, "Planned status"):
            doc.validate()

    def test_native_list_conditions_use_only_permitted_references_and_assignee(self):
        condition = self.permissions.query_conditions()
        self.assertIn("PERMITTED-''1", condition)
        self.assertIn("assigned_to='sales@example.invalid'", condition)
        self.assertEqual(self.frappe.get_list.call_count, 3)
        self.frappe.get_list.return_value = []
        self.assertTrue(self.permissions.query_conditions().startswith("1=0"))
        self.assertEqual(self.permissions.query_conditions("Guest"), "1=0")
