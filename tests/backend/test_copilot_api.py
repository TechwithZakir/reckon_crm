"""The Sales Agent copilot in /crm: read-only, and only on leads and deals (no bench)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]


class CopilotApiTests(unittest.TestCase):
    def test_only_leads_and_deals_and_read_access_first(self):
        source = (ROOT / "reckon_crm" / "api" / "copilot.py").read_text(encoding="utf-8")
        self.assertIn('ALLOWED = ("CRM Lead", "CRM Deal")', source)
        self.assertIn('doc.check_permission("read")', source)

    def test_writes_nothing(self):
        source = (ROOT / "reckon_crm" / "api" / "copilot.py").read_text(encoding="utf-8")
        for write in (".insert(", ".save(", "set_value(", "db_set(", "delete("):
            self.assertNotIn(write, source, write)

    def test_missing_sales_agent_is_explained_not_an_error(self):
        source = (ROOT / "reckon_crm" / "api" / "copilot.py").read_text(encoding="utf-8")
        self.assertIn("except ImportError", source)

    def test_the_tab_is_registered_on_leads_and_deals(self):
        index = (ROOT / "frontend" / "src" / "extensions" / "index.js").read_text(encoding="utf-8")
        self.assertIn("name: 'Copilot'", index)
        self.assertIn("for (const doctype of ['CRM Lead', 'CRM Deal'])", index)


if __name__ == "__main__":
    unittest.main()
