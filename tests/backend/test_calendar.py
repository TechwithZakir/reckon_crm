import importlib
import sys
import types
import unittest
from datetime import date, datetime, time
from unittest.mock import Mock, patch

from test_visit_service import Record


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType("frappe")
        self.frappe.PermissionError = PermissionError
        def throw(message, exception=ValueError):
            raise exception(message)
        self.frappe.throw = throw
        self.frappe.has_permission = Mock(return_value=True)
        self.frappe.db = Record(exists=Mock(return_value=True), has_column=Mock(return_value=True))
        self.event = Record(name="EVENT-1", flags=Record(), meta=Record(has_field=lambda field: True),
                            insert=Mock(), save=Mock())
        object.__setattr__(self.event, "save", Mock())
        self.frappe.new_doc = Mock(return_value=self.event)
        self.frappe.get_doc = Mock(return_value=self.event)
        utils = types.ModuleType("frappe.utils")
        utils.getdate = lambda value: date.fromisoformat(str(value))
        utils.get_time = lambda value: time.fromisoformat(str(value))
        modules = patch.dict(sys.modules, {"frappe": self.frappe, "frappe.utils": utils})
        modules.start(); self.addCleanup(modules.stop)
        self.service = importlib.reload(importlib.import_module("reckon_crm.services.calendar"))
        self.visit = Record(name="VISIT-1", reference_doctype="CRM Lead", reference_name="LEAD-1",
                            planned_date="2026-09-12", status="Planned", assigned_to="sales@example.invalid",
                            visit_purpose="Demo <script>")
        self.visit.db_set = lambda key, value, **kwargs: self.visit.update({key: value})

    def test_date_only_and_timed_events_have_calendar_end(self):
        values = self.service.event_values(self.visit)
        self.assertEqual(values["all_day"], 1)
        self.assertEqual(values["ends_on"], datetime(2026, 9, 12, 23, 59, 59))
        self.assertNotIn("<script>", values["description"])
        self.visit.planned_start_time = "23:30:00"
        values = self.service.event_values(self.visit)
        self.assertEqual(values["ends_on"], datetime(2026, 9, 13, 0, 30))
        self.visit.planned_start_time = "09:00:00"
        self.visit.planned_end_time = "10:30:00"
        self.assertEqual(self.service.event_values(self.visit)["ends_on"].hour, 10)
        self.visit.assigned_to = "Administrator"
        self.assertEqual(self.service.event_values(self.visit)["event_participants"], [])

    def test_sync_reuses_private_event_and_updates_assignee_and_status(self):
        self.service.sync_visit(self.visit)
        self.assertEqual(self.visit.calendar_event, "EVENT-1")
        self.assertEqual(self.event.event_type, "Private")
        self.event.insert.assert_called_once_with()
        self.visit.assigned_to = "other@example.invalid"
        self.visit.status = "Completed"
        self.service.sync_visit(self.visit)
        self.assertEqual(self.event.status, "Completed")
        self.assertEqual(self.event.event_participants[0]["email"], self.visit.assigned_to)
        self.frappe.get_doc.assert_called_with("Event", "EVENT-1", for_update=True)
        self.event.save.assert_called_once_with(ignore_permissions=True)
        self.service.sync_visit(self.visit, status="Cancelled")
        self.assertEqual(self.event.status, "Cancelled")
        self.event.insert.assert_called_once()

    def test_creation_denied_and_external_edits_cannot_forge_sync_flag(self):
        self.frappe.has_permission.return_value = False
        with self.assertRaises(PermissionError):
            self.service.sync_visit(self.visit)
        self.event.insert.assert_not_called()
        self.event.flags.reckon_calendar_sync = True
        with self.assertRaisesRegex(ValueError, "managed by a field visit"):
            self.service.guard_event(self.event)
        self.event.flags.reckon_calendar_sync = self.service.CALENDAR_TOKEN
        self.service.guard_event(self.event)
        self.event.flags.clear()
        self.frappe.db.exists.return_value = False
        self.service.guard_event(self.event)  # Ordinary native events stay editable.

    def test_incompatible_schema_and_failed_insert_do_not_link_visit(self):
        self.event.meta.has_field = lambda field: field != "event_participants"
        with self.assertRaisesRegex(ValueError, "incompatible"):
            self.service.sync_visit(self.visit)
        self.assertIsNone(self.visit.calendar_event)
        self.event.meta.has_field = lambda field: True
        self.event.insert.side_effect = ValueError("Database write failed")
        with self.assertRaisesRegex(ValueError, "Database write failed"):
            self.service.sync_visit(self.visit)
        self.assertIsNone(self.visit.calendar_event)
