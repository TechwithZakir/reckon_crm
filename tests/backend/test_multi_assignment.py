import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from test_visit_service import Record


class MultiAssignmentTests(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType("frappe")
        frappe.session = Record(user="sales@example.invalid")
        frappe.PermissionError = PermissionError
        frappe.whitelist = lambda **kwargs: lambda function: function
        def throw(message, exception=ValueError): raise exception(message)
        frappe.throw = throw
        permissions = types.ModuleType("reckon_crm.utils.permissions")
        permissions.REFERENCES = ("CRM Lead",)
        permissions.logged_in = Mock()
        permissions.is_manager = Mock(return_value=True)
        permissions.reference_doc = Mock()
        service = types.ModuleType("reckon_crm.services.visit_service")
        modules = patch.dict(sys.modules,{"frappe":frappe,"reckon_crm.utils.permissions":permissions,"reckon_crm.services.visit_service":service})
        modules.start(); self.addCleanup(modules.stop)
        self.api = importlib.reload(importlib.import_module("reckon_crm.api.visits"))
        self.permissions = permissions
        self.schedule = patch.object(self.api,"schedule",side_effect=lambda data:{"data":dict(data)}).start()
        self.addCleanup(patch.stopall)

    def test_multi_selection_creates_distinct_assignees_once(self):
        result = self.api.schedule_many({"reference_doctype":"CRM Lead","reference_name":"L1"},["a@example.invalid","b@example.invalid","a@example.invalid"])
        self.assertEqual([v["assigned_to"] for v in result["data"]],["a@example.invalid","b@example.invalid"])
        self.assertEqual(self.schedule.call_count,2)

    def test_nonmanager_cannot_assign_others_and_invalid_batches_rejected(self):
        self.permissions.is_manager.return_value = False
        with self.assertRaises(PermissionError): self.api.schedule_many({},["other@example.invalid"])
        self.schedule.assert_not_called()
        for values in ([], [None], list(map(str,range(26))), {}):
            with self.assertRaises(ValueError): self.api.schedule_many({},values)

    def test_batch_does_not_swallow_failed_schedule(self):
        self.schedule.side_effect = [dict(data={"name":"first"}), PermissionError("denied")]
        with self.assertRaises(PermissionError): self.api.schedule_many({},["a","b"])
