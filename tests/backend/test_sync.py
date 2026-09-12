import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

from test_visit_service import Record


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType("frappe")
        self.frappe.PermissionError = PermissionError
        self.frappe.session = Record(user="sales@example.invalid")
        def throw(message, exception=ValueError):
            raise exception(message)
        self.frappe.throw = throw
        self.frappe.get_installed_apps = Mock(return_value=["frappe", "crm"])
        self.frappe.db = Record(exists=Mock(return_value=True))
        self.frappe.get_all = Mock(return_value=["EMP-1"])
        self.log = Record(name="LOG-1", meta=Record(has_field=lambda field: True), insert=Mock(), set=lambda key, value: self.log.update({key:value}))
        self.frappe.new_doc = Mock(return_value=self.log)
        self.options = {"sync_calendar":0,"sync_tasks":0,"sync_employee_checkin":0,"skip_auto_attendance":1}
        self.frappe.get_single = Mock(return_value=Record(self.options))
        self.calendar = types.ModuleType("reckon_crm.services.calendar")
        self.calendar.sync_visit = Mock()
        self.task = types.ModuleType("reckon_crm.services.task_sync")
        self.task.sync_task = Mock()
        modules = patch.dict(sys.modules, {"frappe":self.frappe, "reckon_crm.services.calendar":self.calendar, "reckon_crm.services.task_sync":self.task})
        modules.start(); self.addCleanup(modules.stop)
        self.settings = importlib.reload(importlib.import_module("reckon_crm.services.settings"))
        self.hrms = importlib.reload(importlib.import_module("reckon_crm.services.hrms_sync"))
        self.sync = importlib.reload(importlib.import_module("reckon_crm.services.sync"))
        self.visit = Record(name="VISIT-1", assigned_to="sales@example.invalid", status="Started", checkin_time="2026-09-12 10:00:00",
            checkin_latitude=0,checkin_longitude=0,geo_status="Within Radius",flags=Record())
        self.visit.db_set = lambda key,value,**kwargs:self.visit.update({key:value})

    def test_disabled_sync_never_touches_optional_apps_or_records(self):
        self.sync.sync_visit(self.visit)
        self.calendar.sync_visit.assert_not_called(); self.task.sync_task.assert_not_called()
        self.frappe.get_all.assert_not_called(); self.frappe.new_doc.assert_not_called()

    def test_switches_route_calendar_and_task_independently(self):
        for key in ("sync_calendar", "sync_tasks"):
            self.frappe.get_single.return_value[key] = 1
        self.sync.sync_visit(self.visit)
        self.calendar.sync_visit.assert_called_once_with(self.visit, None)
        self.task.sync_task.assert_called_once_with(self.visit, None)

    def test_hrms_requirement_actor_mapping_permissions_and_duplicate_prevention(self):
        with self.assertRaisesRegex(ValueError,"HRMS"):
            self.hrms.sync_log(self.visit,"IN",self.options)
        self.frappe.get_installed_apps.return_value.append("hrms")
        self.visit.assigned_to = "someone@example.invalid"
        with self.assertRaises(PermissionError): self.hrms.sync_log(self.visit,"IN",self.options)
        self.visit.assigned_to = self.frappe.session.user
        self.frappe.get_all.return_value = ["EMP-1","EMP-2"]
        with self.assertRaisesRegex(ValueError,"exactly one"): self.hrms.sync_log(self.visit,"IN",self.options)
        self.frappe.get_all.return_value = ["EMP-1"]
        self.log.denied = True
        with self.assertRaises(PermissionError): self.hrms.sync_log(self.visit,"IN",self.options)
        self.log.denied = False
        self.hrms.sync_log(self.visit,"IN",self.options)
        self.assertEqual(self.log.latitude,0); self.assertEqual(self.log.longitude,0)
        self.assertEqual(self.log.log_type,"IN"); self.assertEqual(self.log.skip_auto_attendance,1)
        self.assertEqual(self.visit.employee_checkin,"LOG-1")
        self.hrms.sync_log(self.visit,"IN",self.options)
        self.log.insert.assert_called_once()

    def test_hrms_is_only_called_on_server_marked_transition_and_propagates_failure(self):
        self.frappe.get_single.return_value.sync_employee_checkin = 1
        self.sync.sync_visit(self.visit)
        self.frappe.new_doc.assert_not_called()
        self.visit.flags.reckon_employee_direction = "IN"
        with self.assertRaisesRegex(ValueError,"HRMS"): self.sync.sync_visit(self.visit)
        self.assertIsNone(self.visit.employee_checkin)

    def test_settings_reject_hrms_without_app_and_invalid_switches(self):
        doc = Record(self.options)
        self.settings.validate_settings(doc)
        doc.sync_employee_checkin = 1
        with self.assertRaisesRegex(ValueError,"Install HRMS"): self.settings.validate_settings(doc)
        doc.sync_employee_checkin = 0; doc.sync_tasks = "anything"
        with self.assertRaisesRegex(ValueError,"enabled or disabled"): self.settings.validate_settings(doc)

    def test_unavailable_location_not_written_as_fake_zero(self):
        self.frappe.get_installed_apps.return_value.append("hrms")
        self.visit.geo_status = "Location Unavailable"
        self.hrms.sync_log(self.visit,"IN",self.options)
        self.assertNotIn("latitude",self.log); self.assertNotIn("longitude",self.log)
