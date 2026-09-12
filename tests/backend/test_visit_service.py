"""Fast service tests with a stateful document double; live DB tests are separate."""

import importlib
import sys
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class Record(dict):
    def __getattr__(self, key):
        return self.get(key)

    __setattr__ = dict.__setitem__

    def check_permission(self, permission):
        if self.get("denied"):
            raise PermissionError("denied")

    def save(self):
        self["saves"] = self.get("saves", 0) + 1

    def as_dict(self):
        return dict(self)


class VisitServiceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, 9, 0)
        frappe = types.ModuleType("frappe")
        frappe.session = Record(user="sales@example.invalid")
        frappe.PermissionError = PermissionError
        def throw(message, exception=ValueError):
            raise exception(message)
        frappe.throw = throw
        frappe.get_roles = Mock(return_value=["Sales User"])
        self.reference = Record(doctype="CRM Lead", name="LEAD-1", add_comment=Mock())
        self.location = Record(doctype="CRM Customer Location", name="LOC-1", reference_doctype="CRM Lead",
                               reference_name="LEAD-1", latitude=0, longitude=0, geofence_radius=100)
        self.visit = Record(doctype="CRM Field Visit", name="VISIT-1", reference_doctype="CRM Lead",
                            reference_name="LEAD-1", customer_location="LOC-1", status="Planned",
                            assigned_to=frappe.session.user, flags=Record())
        def get_doc(doctype, name, **kwargs):
            return {"CRM Field Visit": self.visit, "CRM Customer Location": self.location, "CRM Lead": self.reference}[doctype]
        frappe.get_doc = Mock(side_effect=get_doc)
        utils = types.ModuleType("frappe.utils")
        utils.now_datetime = lambda: self.now
        utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(value)
        modules = patch.dict(sys.modules, {"frappe": frappe, "frappe.utils": utils})
        modules.start(); self.addCleanup(modules.stop)
        importlib.reload(importlib.import_module("reckon_crm.utils.permissions"))
        self.service = importlib.reload(importlib.import_module("reckon_crm.services.visit_service"))
        self.frappe = frappe

    def test_complete_lifecycle_snapshots_geofence_and_posts_once(self):
        self.service.check_in("VISIT-1", 0, 0, 5)
        self.assertEqual(self.visit.status, "Started")
        self.assertEqual(self.visit.geo_status, "Within Radius")
        self.assertEqual(self.visit.checkin_by, self.frappe.session.user)
        self.frappe.get_doc.assert_any_call("CRM Field Visit", "VISIT-1", for_update=True)
        self.location.latitude = 50  # Checkout uses the check-in snapshot, not an edited location.
        self.now += timedelta(minutes=42)
        self.service.check_out("VISIT-1", "Interested <script>", latitude=0, longitude=0, accuracy=5)
        self.assertEqual(self.visit.status, "Completed")
        self.assertEqual(self.visit.duration_minutes, 42)
        self.assertEqual(self.visit.checkout_geo_status, "Within Radius")
        self.reference.add_comment.assert_called_once()
        self.assertIn("&lt;script&gt;", self.reference.add_comment.call_args.args[1])
        with self.assertRaises(ValueError):
            self.service.check_out("VISIT-1", "Duplicate")
        self.reference.add_comment.assert_called_once()

    def test_actor_and_reference_permissions_are_enforced(self):
        self.visit.assigned_to = "other@example.invalid"
        with self.assertRaises(PermissionError):
            self.service.check_in("VISIT-1", 0, 0, 5)
        self.visit.assigned_to = self.frappe.session.user
        self.reference.denied = True
        with self.assertRaises(PermissionError):
            self.service.check_in("VISIT-1", 0, 0, 5)
        self.assertEqual(self.visit.status, "Planned")

    def test_unavailable_gps_is_recorded_and_invalid_samples_do_not_start(self):
        with self.assertRaises(ValueError):
            self.service.check_in("VISIT-1", "NaN", 0, 5)
        self.assertEqual(self.visit.status, "Planned")
        self.service.check_in("VISIT-1")
        self.assertEqual(self.visit.geo_status, "Location Unavailable")
        self.assertIsNone(self.visit.checkin_latitude)

    def test_reparented_location_and_invalid_transition_rejected(self):
        self.location.reference_name = "OTHER"
        with self.assertRaises(ValueError):
            self.service.check_in("VISIT-1", 0, 0, 5)
        with self.assertRaises(ValueError):
            self.service.check_out("VISIT-1", "Done")
        self.service.cancel("VISIT-1")
        with self.assertRaises(ValueError):
            self.service.cancel("VISIT-1")

    def test_empty_outcome_does_not_complete(self):
        self.service.check_in("VISIT-1", 0, 0, 5)
        with self.assertRaises(ValueError):
            self.service.check_out("VISIT-1", " ")
        self.assertEqual(self.visit.status, "Started")
        self.reference.add_comment.assert_not_called()

    def test_guest_access_rejected(self):
        self.frappe.session.user = "Guest"
        with self.assertRaises(PermissionError):
            self.service.check_in("VISIT-1")
