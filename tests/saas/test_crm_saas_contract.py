"""Framework-free contract tests for the Reckon CRM SaaS registration.

Run: python -m unittest discover -s tests/saas
"""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from reckon_crm.saas_constants import MODULE_FEATURES, ROLES, TENANT_OWNED_DOCTYPES  # noqa: E402
from reckon_crm.saas_module import get_module_definition  # noqa: E402

REQUIRED = {"key", "label", "workspace", "home_route", "admin_role", "roles", "seed_handler", "subscription_features"}


class CRMSaaSContractTests(unittest.TestCase):
    def setUp(self):
        self.d = get_module_definition()

    def test_required_keys(self):
        self.assertTrue(REQUIRED.issubset(self.d))

    def test_admin_role_is_a_module_role(self):
        self.assertIn(self.d["admin_role"], self.d["roles"])
        self.assertEqual(self.d["roles"], list(ROLES))

    def test_features_match_constants(self):
        self.assertEqual(self.d["subscription_features"], list(MODULE_FEATURES))

    def test_seed_handler_defined(self):
        module_path, function_name = self.d["seed_handler"].rsplit(".", 1)
        self.assertEqual(module_path, "reckon_crm.seed")
        source = (ROOT / "reckon_crm" / "seed.py").read_text(encoding="utf-8")
        self.assertIn(f"def {function_name}(company: str, seed_version: str)", source)

    def test_tenant_doctypes(self):
        self.assertEqual(TENANT_OWNED_DOCTYPES, ("CRM Lead", "CRM Deal", "CRM Organization"))


if __name__ == "__main__":
    unittest.main()
