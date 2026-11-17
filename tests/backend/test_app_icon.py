import json
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "reckon_crm"


class AppIconTests(unittest.TestCase):
    def test_reckon_crm_has_its_own_desk_icon(self):
        hooks = (APP / "hooks.py").read_text(encoding="utf-8")
        self.assertIn('app_logo_url = "/assets/reckon_crm/images/reckon-crm.svg"', hooks)
        self.assertIn('"logo": app_logo_url', hooks)
        icon = (APP / "public" / "images" / "reckon-crm.svg").read_text(encoding="utf-8")
        self.assertIn("<svg", icon)
        self.assertNotIn("crm/images/logo.svg", hooks)  # not Frappe CRM's own logo

    def test_the_release_notes_are_kept(self):
        self.assertTrue((APP.parent / "RELEASE_NOTES.md").is_file())
        json.dumps({})
